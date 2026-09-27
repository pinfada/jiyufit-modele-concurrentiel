"""Réduction du duel à accumulation finie, sous efforts/asymétrie constants.

La dérivation locale est propre à ce dépôt, et ne constitue pas une
identification empirique de r. Voir section XXXIV du notebook.
"""
import numpy as np
from scipy.special import expit


def etape_ratio(rho, r, b, c):
    if not np.isfinite([rho, r, b, c]).all() or min(rho, r, c) <= 0 or b < 0:
        raise ValueError('rho, r, c positifs et b non négatif requis')
    share = expit(np.log(c) + r*np.log(rho))
    return (rho + b*share)/(1+b*(1-share))


def persistance_locale(r, b, share):
    """Dérivée au point fixe : phi = (1+b*r*(1-s))/(1+b*(1-s))."""
    if not np.isfinite([r, b, share]).all() or r <= 0 or b < 0 or not 0 < share < 1:
        raise ValueError('r positif, b non négatif, part strictement intérieure requis')
    weight = b*(1-share)
    return (1+weight*r)/(1+weight)
