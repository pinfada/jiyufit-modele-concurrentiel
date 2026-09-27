"""Évaluer la prévision d'abonnements d'un concurrent à fréquence trimestrielle.

Adaptation descriptive log(N[t+1]) = a + phi*log(N[t]), et non validation
de l'équation de part de marché logit(s) ou du modèle structurel de Tullock.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from outils.inference import ols_hac


def lire_abonnements(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if len(set(reader.fieldnames or [])) != len(reader.fieldnames or []):
            raise ValueError('Colonnes dupliquées')
        if not {'trimestre', 'abonnements'}.issubset(reader.fieldnames or []):
            raise ValueError('Colonnes trimestre et abonnements requises')
        rows = list(reader)
    dates, values, ordinals = [], [], []
    for row in rows:
        if None in row or not re.fullmatch(r'[0-9]{4}-Q[1-4]', row['trimestre'] or ''):
            raise ValueError('Trimestre invalide')
        year, quarter = int(row['trimestre'][:4]), int(row['trimestre'][-1])
        if year < 1: raise ValueError('Année invalide')
        dates.append(row['trimestre']); ordinals.append(year*4+quarter)
        values.append(float(row['abonnements']))
    if len(values) < 12 or any(b-a != 1 for a,b in zip(ordinals, ordinals[1:])):
        raise ValueError('Au moins 12 trimestres consécutifs, triés et uniques requis')
    values = np.asarray(values)
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError('Abonnements strictement positifs et finis requis')
    return dates, values


def prevoir(train, horizon, model):
    train = np.asarray(train, dtype=float)
    if train.ndim != 1 or len(train) < 8 or not np.isfinite(train).all() or np.any(train <= 0):
        raise ValueError('Apprentissage positif et fini sur au moins 8 trimestres')
    if type(horizon) is not int or not 1 <= horizon <= 4:
        raise ValueError('Horizon entre 1 et 4 trimestres')
    if model == 'persistance': return float(train[-1])
    if model == 'saisonnier_naif': return float(train[len(train)+horizon-1-4])
    if model == 'derive_log':
        result = np.exp(np.log(train[-1])+horizon*(np.log(train[-1])-np.log(train[0]))/(len(train)-1))
    elif model in ('ar1_log', 'ar1_log_saisonnier'):
        log_values = np.log(train)
        X = np.column_stack((np.ones(len(train)-1), log_values[:-1]))
        seasonal = model.endswith('saisonnier')
        if seasonal:
            angle = 2*np.pi*np.arange(1, len(train))/4
            X = np.column_stack((X, np.sin(angle), np.cos(angle)))
        if np.linalg.matrix_rank(X) < X.shape[1]: return float(train[-1])
        beta = np.linalg.lstsq(X, log_values[1:], rcond=None)[0]
        current = log_values[-1]
        for step in range(horizon):
            current = beta[0]+beta[1]*current
            if seasonal:
                angle = 2*np.pi*(len(train)+step)/4
                current += beta[2]*np.sin(angle)+beta[3]*np.cos(angle)
        result = np.exp(current)
    else:
        raise ValueError('Modèle inconnu')
    if not np.isfinite(result): raise ValueError('Prévision divergente')
    return float(result)


MODELS = ('persistance', 'saisonnier_naif', 'derive_log', 'ar1_log', 'ar1_log_saisonnier')


def backtest(values, dates, min_train=12):
    if len(values) != len(dates) or min_train < 8 or len(values) < min_train+4:
        raise ValueError('Historique insuffisant pour les horizons communs')
    rows = []
    for h in (1, 2, 4):
        for origin in range(min_train, len(values)-h+1):
            target = origin+h-1
            for model in MODELS:
                prediction = prevoir(values[:origin], h, model)
                rows.append(dict(model=model, horizon_trimestres=h,
                                 origine=dates[origin-1], cible=dates[target],
                                 prediction=prediction, observe=float(values[target]),
                                 erreur=prediction-float(values[target])))
    return rows


def scores(rows):
    result = []
    for horizon in (1, 2, 4):
        for model in MODELS:
            selected = [r for r in rows if r['model'] == model and r['horizon_trimestres'] == horizon]
            errors = np.array([r['erreur'] for r in selected])
            observed = np.array([r['observe'] for r in selected])
            result.append(dict(model=model, horizon_trimestres=horizon, n=len(selected),
                               rmse_abonnements=float(np.sqrt(np.mean(errors**2))),
                               mae_abonnements=float(np.mean(abs(errors))),
                               mape_pourcent=float(np.mean(abs(errors)/observed)*100)))
    return result


def analyser(path, provenance_path):
    dates, values = lire_abonnements(path)
    provenance = json.loads(Path(provenance_path).read_text(encoding='utf-8'))
    sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if provenance.get('source_csv_sha256') != sha or provenance.get('frequence') != 'trimestrielle':
        raise ValueError('Empreinte ou fréquence incompatible avec la provenance')
    log_values = np.log(values)
    beta, cov, residuals = ols_hac(log_values[1:], np.column_stack((np.ones(len(values)-1), log_values[:-1])))
    se_phi = float(np.sqrt(max(0, cov[1, 1])))
    ci = [float(beta[1]-1.96*se_phi), float(beta[1]+1.96*se_phi)]
    predictions = backtest(values, dates)
    recent = [i for i,d in enumerate(dates) if d >= '2022-Q1']
    sensitivity = scores(backtest(values[recent], [dates[i] for i in recent], min_train=8)) if len(recent) >= 12 else []
    r2 = 1-float(residuals@residuals)/float(np.sum((log_values[1:]-log_values[1:].mean())**2))
    report = dict(entreprise=provenance['entreprise'], debut=dates[0], fin=dates[-1], n=len(values),
                  frequence='trimestrielle', csv_sha256=sha, equation='log(N[t+1]) = a + phi*log(N[t])',
                  phi=float(beta[1]), phi_hac95_approximatif=ci, r2_ajustement=r2,
                  plateau_stationnaire_etabli=False,
                  scores=scores(predictions), sensibilite_depuis_2022=sensitivity,
                  validation_structurelle=False,
                  limites=['Adaptation sur un effectif : aucune part de marché observée.',
                           'HAC asymptotique sur petit échantillon ; proche unité et ruptures possibles.',
                           'Les erreurs sont rétrospectives ; valeurs publiées dans des rapports ultérieurs.',
                           'COVID, acquisitions et expansion modifient la dynamique.',
                           'Comparaison exploratoire, aucun transfert automatique de phi à JiyuFit.'])
    return report, predictions


def executer(path, provenance_path, sortie):
    report, predictions = analyser(path, provenance_path)
    sortie = Path(sortie); sortie.mkdir(parents=True, exist_ok=True)
    if Path(path).resolve().parent == sortie.resolve():
        raise ValueError('Séparer les résultats des sources')
    (sortie/'resultats.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    for name, rows in [('scores.csv', report['scores']), ('predictions.csv', predictions)]:
        with (sortie/name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dates, values = lire_abonnements(path)
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), layout='constrained')
    colors = dict(ar1_log='#1f77b4', persistance='#ff7f0e', derive_log='#2ca02c',
                  saisonnier_naif='#9467bd', ar1_log_saisonnier='#d62728')
    axes[0].plot(dates, values/1e6, 'ko-', label='abonnements publiés')
    for model in ('ar1_log', 'persistance', 'derive_log'):
        rows = [r for r in predictions if r['model'] == model and r['horizon_trimestres'] == 1]
        axes[0].plot([r['cible'] for r in rows], [r['prediction']/1e6 for r in rows], '--',
                     color=colors[model], label=model+' (1 trimestre)')
    axes[0].set_ylabel("Millions d'abonnements")
    axes[0].tick_params(axis='x', rotation=65, labelsize=7)
    axes[0].set_title('Basic-Fit — données officielles, prévisions chronologiques')
    axes[0].legend(fontsize=8)
    x = np.arange(3)
    for i,model in enumerate(MODELS):
        ss = [r for r in report['scores'] if r['model']==model]
        axes[1].bar(x+(i-2)*.15, [r['rmse_abonnements']/1000 for r in ss], width=.15,
                    color=colors[model], label=model)
    axes[1].set_xticks(x, ['1 trimestre', '2 trimestres', '4 trimestres'])
    axes[1].set_ylabel("RMSE (milliers d'abonnements)")
    axes[1].legend(fontsize=8)
    fig.savefig(sortie/'validation.png', dpi=140); plt.close(fig)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--sortie', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = executer(args.csv, args.provenance, args.sortie)
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))
    print(f"{report['n']} trimestres : {report['debut']} à {report['fin']}")
    print(f"Phi trimestriel log-effectif = {report['phi']:.4f} ; HAC approximatif {report['phi_hac95_approximatif']}")
    for row in report['scores']:
        print(f"h={row['horizon_trimestres']} {row['model']}: RMSE={row['rmse_abonnements']:.0f}, n={row['n']}")
    print('Test prédictif partiel ; validation structurelle de JiyuFit : non établie.')


if __name__ == '__main__':
    main()
