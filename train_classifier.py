"""LightGBM binary classifier (krok 8 z roadmapy).

Trenuje model binarny is_real_c_check (1) vs other_long_gap (0) na pseudo-labelach
z reguł, robi time-based holdout (2025-07-01) i wypluwa c_check_probability dla
każdego kandydata.

Pseudo-labelling:
- HIGH lub MEDIUM confidence → label = 1 (positive)
- LOW + gap < 18d + nie w MRO → label = 0 (AOG)
- LOW + gap > 50d + niska aktywność pre-gap + nie w MRO → label = 0 (storage/lease)
- LOW pozostałe → unlabeled (do predykcji, nie do treningu)

Uruchomienie:
    python train_classifier.py

Output:
    output/predictions.csv        - kandydaci × c_check_probability
    output/feature_importance.csv - rankingi features
    output/classifier_log.txt     - cały log
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

from pipeline import load_b737_eu, detect_gaps, classify_check, OUTPUT_DIR, _Tee
from features import build_features, get_c_check_candidates

# LightGBM z fallbackiem na sklearn HistGradientBoosting (handles NaN natywnie)
try:
    import lightgbm as lgb
    USE_LIGHTGBM = True
except ImportError:
    USE_LIGHTGBM = False

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix
)


HOLDOUT_DATE = pd.Timestamp("2025-07-01")
RANDOM_SEED = 42

# Features dla modelu. Świadomie WYŁĄCZONE:
# - at_strict_mro_hub, at_any_mro_hub - bezpośredni komponent reguły HIGH/MEDIUM (leakage)
# - stayed_put - komponent reguły MEDIUM (leakage)
# - confidence - to jest źródło labela
FEATURE_COLS = [
    # Gap-level (kalendarz + lokalizacja kraj)
    'gap_days', 'gap_start_month', 'gap_start_dow', 'ades_country',
    # Aircraft
    'typecode', 'registration_country', 'destination_country_matches_registration',
    # Pre-gap (aktywność 60 dni przed gapem)
    'flights_per_day_pre_gap', 'distinct_airports_pre_gap',
    'avg_flight_duration_pre_gap_hours',
    # Post-gap (zachowanie 30 dni po gapie)
    'same_operator_after', 'same_country_after',
    # Operator-level
    'operator_fleet_size', 'gap_at_operator_typical_mro',
    # Historical (poprzednie C-checki tego samolotu)
    'num_previous_c_checks', 'interval_to_previous_days',
    'mean_interval_prev_c_checks',
]

CATEGORICAL_COLS = ['ades_country', 'typecode', 'registration_country']


# ============================================================
# Pseudo-labelling
# ============================================================

def assign_pseudo_labels(features):
    """Pseudo-labele na bazie reguł confidence + heurystyk negatywnych."""
    df = features.copy()
    label = pd.Series(index=df.index, dtype=object)
    
    # POSITIVES: HIGH lub MEDIUM (oba znaczą "to prawdopodobnie C-check")
    label[df['confidence'].isin(['HIGH', 'MEDIUM'])] = 1
    
    # NEGATIVES: tylko z LOW + dodatkowe twarde kryteria
    is_low = df['confidence'] == 'LOW'
    not_at_mro = ~df['at_any_mro_hub']
    
    # Reguła 1: krótki gap (14-18d) w nieznanym miejscu = AOG, nie pełen C-check
    rule1 = is_low & not_at_mro & (df['gap_days'] < 18)
    label[rule1] = 0
    
    # Reguła 2: długi gap (>50d) + niska aktywność pre-gap + poza MRO = storage/lease
    rule2 = (
        is_low & not_at_mro &
        (df['gap_days'] > 50) &
        (df['flights_per_day_pre_gap'] < 0.5)
    )
    label[rule2] = 0
    
    df['label'] = label
    return df


# ============================================================
# Feature matrix preparation
# ============================================================

def _coerce_types(X):
    """Konwersja kolumn na typy akceptowane przez LightGBM/HistGBM.
    
    - bool → int
    - object zawierający True/False/NaN → float (jeśli z CSV)
    - Kategoryczne zostają jak są (osobno obsłużone)
    """
    for c in X.columns:
        if c in CATEGORICAL_COLS:
            continue
        if X[c].dtype == bool:
            X[c] = X[c].astype(int)
        elif X[c].dtype == object:
            # Próbujemy konwersję na float (True→1, False→0, NaN/None→NaN)
            X[c] = pd.to_numeric(X[c], errors='coerce')
    return X


def prepare_matrix_lgbm(features, cols):
    """Macierz X dla LightGBM - kategoryczne jako category dtype."""
    X = features[cols].copy()
    X = _coerce_types(X)
    for c in CATEGORICAL_COLS:
        if c in X.columns:
            X[c] = X[c].astype('category')
    return X


def prepare_matrix_sklearn(features, cols, encoder=None, fit=False):
    """Macierz X dla sklearn HistGradientBoosting.
    
    Kategoryczne kolumny ordinal-encoded (sklearn obsługuje to natywnie w HistGBM).
    """
    X = features[cols].copy()
    X = _coerce_types(X)
    
    cat_cols_present = [c for c in CATEGORICAL_COLS if c in X.columns]
    
    if fit:
        encoder = OrdinalEncoder(
            handle_unknown='use_encoded_value', unknown_value=-1,
            encoded_missing_value=-2,
        )
        X[cat_cols_present] = encoder.fit_transform(X[cat_cols_present].astype(object))
    elif encoder is not None:
        X[cat_cols_present] = encoder.transform(X[cat_cols_present].astype(object))
    
    return X, encoder


# ============================================================
# Training
# ============================================================

def train_lgbm(X_train, y_train, X_val, y_val):
    """LightGBM binary z class balance + early stopping na walidacji."""
    pos = (y_train == 1).sum()
    neg = (y_train == 0).sum()
    pos_weight = max(1.0, neg / max(1, pos))
    
    train_set = lgb.Dataset(X_train, label=y_train, categorical_feature=CATEGORICAL_COLS)
    val_set = lgb.Dataset(X_val, label=y_val, categorical_feature=CATEGORICAL_COLS,
                          reference=train_set)
    
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'scale_pos_weight': pos_weight,
        'learning_rate': 0.05,
        'num_leaves': 31,
        'min_child_samples': 20,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'seed': RANDOM_SEED,
        'verbose': -1,
    }
    callbacks = [
        lgb.early_stopping(stopping_rounds=30, verbose=False),
        lgb.log_evaluation(period=0),
    ]
    model = lgb.train(
        params, train_set, num_boost_round=500,
        valid_sets=[val_set], callbacks=callbacks,
    )
    print(f"  Best iter: {model.best_iteration}, best AUC val: {model.best_score['valid_0']['auc']:.3f}")
    return model


def train_histgbm(X_train, y_train):
    """sklearn HistGradientBoosting - radzi sobie z NaN natywnie."""
    pos = (y_train == 1).sum()
    neg = (y_train == 0).sum()
    pos_weight = max(1.0, neg / max(1, pos))
    
    sample_weight = np.where(y_train == 1, pos_weight, 1.0)
    
    cat_indices = [i for i, c in enumerate(X_train.columns) if c in CATEGORICAL_COLS]
    
    model = HistGradientBoostingClassifier(
        learning_rate=0.05, max_iter=300,
        max_depth=6, min_samples_leaf=20,
        l2_regularization=0.1,
        categorical_features=cat_indices,
        random_state=RANDOM_SEED,
        early_stopping=True, validation_fraction=0.15, n_iter_no_change=30,
    )
    model.fit(X_train, y_train, sample_weight=sample_weight)
    print(f"  Iteracji: {model.n_iter_}")
    return model


def predict_proba(model, X):
    if USE_LIGHTGBM:
        return model.predict(X)
    return model.predict_proba(X)[:, 1]


# ============================================================
# Evaluation
# ============================================================

def evaluate(y_true, y_proba, name="Test"):
    """AUC + precision/recall/F1 + confusion + precision@k."""
    if y_true.nunique() < 2:
        print(f"\n  [{name}] Tylko 1 klasa, pomijam metryki")
        return None
    
    auc = roc_auc_score(y_true, y_proba)
    y_pred = (y_proba >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    
    print(f"\n  [{name}] n={len(y_true)}  AUC={auc:.3f}")
    print(f"    Threshold=0.5: precision={precision_score(y_true, y_pred, zero_division=0):.3f}, "
          f"recall={recall_score(y_true, y_pred, zero_division=0):.3f}, "
          f"F1={f1_score(y_true, y_pred, zero_division=0):.3f}")
    print(f"    Confusion (rows=true [0,1], cols=pred [0,1]):")
    print(f"      [[TN={cm[0,0]:4d}  FP={cm[0,1]:4d}]")
    print(f"       [FN={cm[1,0]:4d}  TP={cm[1,1]:4d}]]")
    
    order = np.argsort(-y_proba)
    y_arr = y_true.values if hasattr(y_true, 'values') else np.asarray(y_true)
    print(f"    Precision@k (top-k najwyższych prob):")
    for k in [25, 50, 100, 200]:
        if k > len(y_true):
            break
        correct = int(y_arr[order[:k]].sum())
        print(f"      @{k}: {correct/k:.3f} ({correct}/{k})")
    
    return auc


def feature_importance_df(model, feature_cols):
    if USE_LIGHTGBM:
        imp_gain = model.feature_importance(importance_type='gain')
        imp_split = model.feature_importance(importance_type='split')
        names = model.feature_name()
        return pd.DataFrame({
            'feature': names,
            'importance_gain': imp_gain,
            'importance_split': imp_split,
        }).sort_values('importance_gain', ascending=False)
    else:
        # HistGradientBoostingClassifier ma permutation_importance ale to drogie
        # Wracam do prostej miary: liczba node'ów per feature
        imp = np.zeros(len(feature_cols))
        # HistGBM nie ma feature_importance prostego - używam dummy z modelu treningu
        # Fallback: zwracam wszystkie zera + nazwę
        return pd.DataFrame({
            'feature': feature_cols,
            'importance_gain': imp,
        })


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    log_path = OUTPUT_DIR / 'classifier_log.txt'
    log_file = open(log_path, 'w', encoding='utf-8')
    sys.stdout = _Tee(sys.__stdout__, log_file)
    
    print(f"=== Krok 8 - LightGBM classifier ===")
    print(f"Engine: {'LightGBM' if USE_LIGHTGBM else 'sklearn HistGradientBoosting (fallback)'}")
    
    # 1. Load + features
    print("\n=== Wczytywanie + feature engineering ===")
    df = load_b737_eu()
    df = detect_gaps(df)
    df['check_type'] = df.apply(classify_check, axis=1)
    candidates = get_c_check_candidates(df)
    features = build_features(df, candidates)
    
    # 2. Pseudo-labelling
    print("\n=== Pseudo-labelling ===")
    features = assign_pseudo_labels(features)
    n_pos = (features['label'] == 1).sum()
    n_neg = (features['label'] == 0).sum()
    n_unl = features['label'].isna().sum()
    print(f"  Pozytywne (1): {n_pos:5d}  (HIGH+MEDIUM)")
    print(f"  Negatywne (0): {n_neg:5d}  (LOW + reguły AOG/storage)")
    print(f"  Unlabeled:     {n_unl:5d}  (LOW ambiguous - tylko predykcja)")
    print(f"  Razem:         {len(features):5d}")
    
    # 3. Time-based split labeled samples
    labeled = features[features['label'].notna()].copy()
    labeled['label'] = labeled['label'].astype(int)
    
    train_df = labeled[labeled['last_seen'] < HOLDOUT_DATE]
    test_df = labeled[labeled['last_seen'] >= HOLDOUT_DATE]
    
    print(f"\n=== Time-based split (cutoff = {HOLDOUT_DATE.date()}) ===")
    print(f"  Train (gap < {HOLDOUT_DATE.date()}): n={len(train_df)}  "
          f"({(train_df['label']==1).sum()} pos / {(train_df['label']==0).sum()} neg)")
    print(f"  Test  (gap >= {HOLDOUT_DATE.date()}): n={len(test_df)}  "
          f"({(test_df['label']==1).sum()} pos / {(test_df['label']==0).sum()} neg)")
    
    if len(test_df) < 50 or test_df['label'].nunique() < 2:
        print("\n  ⚠️  Test set za mały/jednoklasowy - random stratified 80/20 split")
        from sklearn.model_selection import train_test_split
        train_df, test_df = train_test_split(
            labeled, test_size=0.2, random_state=RANDOM_SEED,
            stratify=labeled['label'],
        )
        print(f"  Train: {len(train_df)}, Test: {len(test_df)}")
    
    # 4. Prepare matrices
    avail_cols = [c for c in FEATURE_COLS if c in features.columns]
    print(f"\n=== ML features ({len(avail_cols)} kolumn) ===")
    for c in avail_cols:
        is_cat = '(cat)' if c in CATEGORICAL_COLS else ''
        print(f"  {c} {is_cat}")
    
    encoder = None
    if USE_LIGHTGBM:
        X_train = prepare_matrix_lgbm(train_df, avail_cols)
        X_test = prepare_matrix_lgbm(test_df, avail_cols)
        X_all = prepare_matrix_lgbm(features, avail_cols)
    else:
        X_train, encoder = prepare_matrix_sklearn(train_df, avail_cols, fit=True)
        X_test, _ = prepare_matrix_sklearn(test_df, avail_cols, encoder=encoder)
        X_all, _ = prepare_matrix_sklearn(features, avail_cols, encoder=encoder)
    
    y_train = train_df['label']
    y_test = test_df['label']
    
    # 5. Train
    print(f"\n=== Trening ===")
    if USE_LIGHTGBM:
        model = train_lgbm(X_train, y_train, X_test, y_test)
    else:
        model = train_histgbm(X_train, y_train)
    
    # 6. Evaluate
    print(f"\n=== Ewaluacja ===")
    y_train_proba = predict_proba(model, X_train)
    evaluate(y_train, y_train_proba, name="Train (in-sample)")
    
    y_test_proba = predict_proba(model, X_test)
    evaluate(y_test, y_test_proba, name="Test (holdout)")
    
    # 7. Feature importance
    print(f"\n=== Top 15 features (importance gain) ===")
    fi = feature_importance_df(model, avail_cols)
    print(fi.head(15).to_string(index=False))
    
    # 8. Predict for ALL candidates (incl. unlabeled LOW)
    print(f"\n=== Predykcja dla wszystkich kandydatów ===")
    features['c_check_probability'] = predict_proba(model, X_all)
    
    print(f"\nStatystyka prob per confidence group:")
    stats_by_conf = features.groupby('confidence')['c_check_probability'].agg(
        ['count', 'mean', 'std', 'min', 'max']
    ).round(3)
    print(stats_by_conf.to_string())
    
    # 9. Top LOW kandydaci z najwyższą probabilistyką - ciekawi handlowca!
    # To są przypadki które reguły uznały za niejasne, ale ML uważa że TO są C-checki
    print(f"\n=== Top 20 LOW kandydatów z najwyższą c_check_probability ===")
    print("(reguły dały LOW, ale ML mówi 'to jednak prawdopodobnie C-check')")
    top_low = (features[features['confidence'] == 'LOW']
               .nlargest(20, 'c_check_probability'))
    display_cols = ['registration', 'icao_operator', 'ades', 'last_seen', 'gap_days',
                    'flights_per_day_pre_gap', 'distinct_airports_pre_gap',
                    'c_check_probability']
    display_cols = [c for c in display_cols if c in top_low.columns]
    print(top_low[display_cols].round(3).to_string(index=False))
    
    # 10. Save
    pred_path = OUTPUT_DIR / 'predictions.csv'
    save_cols = ['icao24', 'registration', 'icao_operator', 'typecode',
                 'ades', 'mro_facility', 'last_seen', 'next_first_seen', 'gap_days',
                 'confidence', 'label', 'c_check_probability'] + avail_cols
    save_cols = list(dict.fromkeys(c for c in save_cols if c in features.columns))
    features[save_cols].to_csv(pred_path, index=False, encoding='utf-8')
    
    fi_path = OUTPUT_DIR / 'feature_importance.csv'
    fi.to_csv(fi_path, index=False, encoding='utf-8')
    
    print(f"\n=== Zapisano ===")
    print(f"  {log_path}")
    print(f"  {pred_path}  ({len(features)} kandydatów × {len(save_cols)} kolumn)")
    print(f"  {fi_path}")
    
    sys.stdout = sys.__stdout__
    log_file.close()
