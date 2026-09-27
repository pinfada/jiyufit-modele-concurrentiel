"""Inférence exploratoire sur les proxys, distincte du r structurel de Tullock.

Références et hypothèses : docs/FONDEMENTS_SCIENTIFIQUES.md.
Les intervalles HAC/IV sont asymptotiques, le bootstrap suppose la stationnarité.
Aucune de ces procédures ne certifie un régime économique près de phi = 1.
"""
import numpy as np
from scipy.special import expit, logit
from scipy.stats import chi2


def serie_finie(values, minimum=4):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < minimum or not np.all(np.isfinite(x)):
        raise ValueError(f"Il faut une série finie unidimensionnelle d'au moins {minimum} points")
    return x


def hac_cov_scores(scores, lags=None):
    """Somme des covariances de scores, noyau Bartlett (Newey–West).

    Renvoie le 'meat' du sandwich, non divisé par n. Les scores ne sont pas
    recentrés ici : l'appelant fournit les résidus de sa régression.
    """
    scores = np.asarray(scores, dtype=float)
    if scores.ndim == 1:
        scores = scores[:, None]
    n = len(scores)
    if n < 2 or not np.all(np.isfinite(scores)):
        raise ValueError("Scores HAC invalides")
    if lags is None:
        lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    if not isinstance(lags, (int, np.integer)) or not 0 <= lags < n:
        raise ValueError("Le nombre de retards HAC doit être compris entre 0 et n-1")
    meat = scores.T @ scores
    for lag in range(1, lags + 1):
        cross = scores[lag:].T @ scores[:-lag]
        meat += (1 - lag / (lags + 1)) * (cross + cross.T)
    return meat


def ols_hac(y, design, lags=None):
    y = serie_finie(y)
    X = np.asarray(design, dtype=float)
    if X.ndim != 2 or len(X) != len(y) or not np.all(np.isfinite(X)):
        raise ValueError("Matrice de régression invalide")
    n, p = X.shape
    if n <= p or np.linalg.matrix_rank(X) < p:
        raise ValueError("Régression non identifiable")
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    residuals = y - X @ beta
    bread = np.linalg.inv(X.T @ X)
    covariance = bread @ hac_cov_scores(X * residuals[:, None], lags) @ bread
    covariance *= n / (n - p)
    return beta, covariance, residuals


def moyenne_hac(values, lags=None):
    values = serie_finie(values)
    mean = float(values.mean())
    variance = float(hac_cov_scores(values - mean, lags)[0, 0]) / len(values)**2
    variance *= len(values) / (len(values) - 1)
    return mean, float(np.sqrt(max(0, variance)))


def lag_triplets(values):
    """Chaque ligne contient un vrai (L_t, L_{t-1}, L_{t-2})."""
    L = serie_finie(values, minimum=6)
    return np.column_stack((L[2:], L[1:-1], L[:-2]))


def iv_from_triplets(rows):
    rows = np.asarray(rows, dtype=float)
    if rows.ndim != 2 or rows.shape[1] != 3 or len(rows) < 3:
        return float('nan')
    if not np.all(np.isfinite(rows)):
        return float('nan')
    y, x, z = (rows - rows.mean(axis=0)).T
    denominator = z @ x
    scale = np.linalg.norm(z) * np.linalg.norm(x)
    if scale == 0 or abs(denominator) <= 1e-12 * scale:
        return float('nan')
    return float((z @ y) / denominator)


def block_indices(n, block_size, rng):
    """Blocs mobiles : le dernier départ n-block_size est inclus."""
    if not isinstance(block_size, (int, np.integer)) or not 1 <= block_size <= n:
        raise ValueError("Taille de bloc invalide")
    starts = rng.integers(0, n - block_size + 1, size=int(np.ceil(n / block_size)))
    return (starts[:, None] + np.arange(block_size)).ravel()[:n]


def bootstrap_iv(values, B=1999, block_size=8, seed=123):
    """Rééchantillonne les triplets déjà construits, jamais les niveaux recollés.

    Des tirages non identifiés restent NaN et sont comptés dans le résumé.
    Les percentiles sont exploratoires ; ce n'est ni une p-valeur ni une
    probabilité a posteriori du régime. Limites près de l'unité : Hansen (1999).
    """
    if not isinstance(B, int) or B < 1:
        raise ValueError("B doit être un entier positif")
    rows = lag_triplets(values)
    rng = np.random.default_rng(seed)
    return np.array([iv_from_triplets(rows[block_indices(len(rows), block_size, rng)])
                     for _ in range(B)])


def bootstrap_summary(draws):
    draws = np.asarray(draws, dtype=float)
    if draws.ndim != 1 or not len(draws):
        raise ValueError("Aucun tirage")
    finite = draws[np.isfinite(draws)]
    return dict(n=len(draws), invalid=int(len(draws) - len(finite)),
                median=float(np.median(finite)) if len(finite) else np.nan,
                interval=tuple(np.quantile(finite, [.025, .975])) if len(finite) else (np.nan, np.nan),
                fraction_ge_1=float(np.mean(finite >= 1)) if len(finite) else np.nan)


def quadratic_set(a, b, c):
    """Ensemble réel {x: ax²+bx+c <= 0}, sans troncature à une grille."""
    scale = max(abs(a), abs(b), abs(c))
    if scale == 0:
        return [(-np.inf, np.inf)]
    a, b, c = a / scale, b / scale, c / scale
    tol = 1e-12
    if abs(a) < tol:
        if abs(b) < tol:
            return [(-np.inf, np.inf)] if c <= 0 else []
        root = -c / b
        return [(-np.inf, root)] if b > 0 else [(root, np.inf)]
    disc = b*b - 4*a*c
    if disc < -tol:
        return [(-np.inf, np.inf)] if a < 0 else []
    if abs(disc) <= tol:
        root = -b / (2*a)
        return [(root, root)] if a > 0 else [(-np.inf, np.inf)]
    q = -.5 * (b + np.copysign(np.sqrt(disc), b))
    lo, hi = sorted((q / a, c / q))
    return [(lo, hi)] if a > 0 else [(-np.inf, lo), (hi, np.inf)]


def iv_diagnostic(values, confidence=.95, lags=None):
    """IV lag2 et ensemble Anderson–Rubin avec covariance HAC.

    Pour chaque phi0 : régresser y-phi0*x sur (1,z), tester le coefficient
    de z. L'inversion du test est quadratique : ensembles disjoints/non bornés
    conservés. Robustesse aux instruments faibles sous validité de z et
    régularité stationnaire ; pas de garantie uniforme près de l'unité.
    """
    if not 0 < confidence < 1:
        raise ValueError("Niveau de confiance invalide")
    rows = lag_triplets(values)
    estimate = iv_from_triplets(rows)
    y, x, z = rows.T
    n = len(z)
    zc = z - z.mean()
    szz = zc @ zc
    if szz <= np.finfo(float).eps * max(1., z @ z):
        return dict(phi_iv=estimate, first_stage_f=0., confidence_set=[(-np.inf, np.inf)],
                    unit_compatible=True, n=n)
    design = np.column_stack((np.ones(n), z))
    by = np.linalg.lstsq(design, y, rcond=None)[0]
    bx = np.linalg.lstsq(design, x, rcond=None)[0]
    # Influence du coefficient de z des deux régressions réduites.
    influence = np.column_stack((zc * (y - design @ by), zc * (x - design @ bx))) / szz
    covariance = hac_cov_scores(influence, lags) * n / (n - 2)
    vyy, vxx, vyx = covariance[0, 0], covariance[1, 1], covariance[0, 1]
    critical = chi2.ppf(confidence, 1)
    accepted = quadratic_set(bx[1]**2 - critical*vxx,
                             -2*by[1]*bx[1] + 2*critical*vyx,
                             by[1]**2 - critical*vyy)
    first_stage = float(bx[1]**2 / vxx) if vxx > 0 else (np.inf if bx[1] != 0 else 0.)
    return dict(phi_iv=estimate, first_stage_f=first_stage, confidence_set=accepted,
                unit_compatible=any(lo <= 1 <= hi for lo, hi in accepted), n=n)


def pooled_iv(series):
    """IV à intercept par duel : sommes de produits centrés, sans poids ddof."""
    num = den = scale = 0.
    for values in series:
        rows = lag_triplets(values)
        y, x, z = (rows - rows.mean(axis=0)).T
        num += z @ y
        den += z @ x
        scale += np.linalg.norm(z) * np.linalg.norm(x)
    return float(num / den) if scale > 0 and abs(den) > 1e-12*scale else np.nan


def panel_bootstrap_iv(series, months, B=1999, block_size=8, seed=11):
    """Blocs calendaires synchronisés entre duels, avec masques d'observation.

    Le pooling impose un phi commun : c'est une hypothèse, pas une conclusion.
    Les triplets restent intacts, y compris aux raccords des blocs. Les duels
    partageant un choc au même mois ne sont pas rééchantillonnés indépendamment.
    """
    if len(series) != len(months) or not series or not isinstance(B, int) or B < 1:
        raise ValueError("Panel invalide")
    from outils.donnees import valider_mois
    for L, dates in zip(series, months):
        valider_mois(dates)
        if len(L) != len(dates):
            raise ValueError("Dates et observations de longueurs différentes")
    calendar = sorted(set(m for dates in months for m in dates[2:]))
    valider_mois(calendar)
    lookup = {m: i for i, m in enumerate(calendar)}
    panel = np.full((len(calendar), len(series), 3), np.nan)
    for j, (L, dates) in enumerate(zip(series, months)):
        for row, date in zip(lag_triplets(L), dates[2:]):
            panel[lookup[date], j] = row
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(B):
        sampled = panel[block_indices(len(panel), block_size, rng)]
        num = den = scale = 0.
        for j in range(len(series)):
            rows = sampled[:, j]
            rows = rows[np.all(np.isfinite(rows), axis=1)]
            if len(rows) < 3:
                num = np.nan
                break
            y, x, z = (rows - rows.mean(axis=0)).T
            num += z @ y
            den += z @ x
            scale += np.linalg.norm(z) * np.linalg.norm(x)
        draws.append(num / den if scale > 0 and abs(den) > 1e-12*scale else np.nan)
    return np.array(draws)


def forecast_logit(L, months, future_months, seasonal=False):
    """AR(1) prédictif ; saisonnalité harmonique annuelle préspécifiée."""
    L = serie_finie(L, minimum=8)
    months = np.asarray(months)
    future_months = np.asarray(future_months)
    if len(months) != len(L) or np.any((months < 1) | (months > 12)):
        raise ValueError("Calendrier invalide")
    X = np.column_stack((np.ones(len(L)-1), L[:-1]))
    if seasonal:
        angle = 2*np.pi*months[1:]/12
        X = np.column_stack((X, np.sin(angle), np.cos(angle)))
    if np.linalg.matrix_rank(X) < X.shape[1]:
        # Série constante : la persistance est une prévision définie.
        return np.full(len(future_months), expit(L[-1]))
    beta = np.linalg.lstsq(X, L[1:], rcond=None)[0]
    current, out = L[-1], []
    for month in future_months:
        current = beta[0] + beta[1]*current
        if seasonal:
            current += beta[2]*np.sin(2*np.pi*month/12) + beta[3]*np.cos(2*np.pi*month/12)
        out.append(expit(current))
    return np.asarray(out)


def rolling_backtest(shares, months, min_train=30, horizons=(1, 3, 6)):
    """Origines croissantes, mêmes cibles par modèle, aucun ajustement futur.

    Les modèles ne sont pas sélectionnés sur ces erreurs ; comparaison
    exploratoire sur données déjà examinées, pas nouvel échantillon vierge.
    """
    s = serie_finie(shares, minimum=min_train+max(horizons))
    if np.any((s <= 0) | (s >= 1)) or min_train < 12:
        raise ValueError("Parts strictement intérieures et apprentissage >= 12 requis")
    m = np.asarray(months)
    if len(m) != len(s):
        raise ValueError("Calendrier de longueur incorrecte")
    L = logit(s)
    results = []
    for horizon in horizons:
        if not isinstance(horizon, int) or not 1 <= horizon <= 12:
            raise ValueError("Horizon mensuel entre 1 et 12 requis")
        for origin in range(min_train, len(s)-horizon+1):
            target = origin+horizon-1
            predictions = {
                'persistance': s[origin-1],
                'saisonnier_naif': s[target-12],
                'derive': expit(L[origin-1] + horizon*(L[origin-1]-L[0])/(origin-1)),
                'ar1': forecast_logit(L[:origin], m[:origin], m[origin:target+1])[-1],
                'ar1_saisonnier': forecast_logit(L[:origin], m[:origin], m[origin:target+1], True)[-1],
            }
            for name, pred in predictions.items():
                results.append(dict(model=name, horizon=horizon, origin=origin,
                                    target=target, prediction=float(pred), observed=float(s[target]),
                                    error=float(pred-s[target])))
    return results


def backtest_scores(results):
    scores = []
    for horizon, model in sorted({(r['horizon'], r['model']) for r in results}):
        errors = np.array([r['error'] for r in results if r['horizon'] == horizon and r['model'] == model])
        scores.append(dict(horizon=horizon, model=model, n=len(errors),
                           rmse=float(np.sqrt(np.mean(errors**2))), mae=float(np.mean(abs(errors)))))
    return scores
