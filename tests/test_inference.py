import unittest
import numpy as np
from scipy.special import expit
from outils.inference import (block_indices, lag_triplets, bootstrap_iv, bootstrap_summary,
    iv_diagnostic, iv_from_triplets, panel_bootstrap_iv, ols_hac, quadratic_set,
    rolling_backtest, backtest_scores, pooled_iv)
from outils.dynamique_reduite import etape_ratio, persistance_locale


class InferenceTests(unittest.TestCase):
    def test_bootstrap_preserves_exact_ar_equation(self):
        # Oracle : y = .12 + .94*x reste vrai dans TOUT sous-échantillon de triplets.
        L = [5.]
        for _ in range(79):
            L.append(.12+.94*L[-1])
        draws = bootstrap_iv(L, B=100, block_size=8)
        np.testing.assert_allclose(draws, .94, atol=1e-10)

    def test_last_block_start_is_included(self):
        rng = np.random.default_rng(44)
        starts = {block_indices(10, 8, rng)[0] for _ in range(100)}
        self.assertEqual(starts, {0, 1, 2})
        np.testing.assert_array_equal(block_indices(5, 5, rng), np.arange(5))

    def test_nonidentified_draws_are_reported(self):
        summary = bootstrap_summary(bootstrap_iv(np.ones(30), B=20))
        self.assertEqual(summary['invalid'], 20)
        self.assertTrue(np.isnan(summary['median']))
        d = iv_diagnostic(np.ones(30))
        self.assertEqual(d['confidence_set'], [(-np.inf, np.inf)])
        self.assertTrue(d['unit_compatible'])

    def test_quadratic_sets_can_be_disjoint_unbounded_empty(self):
        self.assertEqual(quadratic_set(1, 0, -1), [(-1., 1.)])
        self.assertEqual(quadratic_set(-1, 0, 1), [(-np.inf, -1.), (1., np.inf)])
        self.assertEqual(quadratic_set(1, 0, 1), [])
        self.assertEqual(quadratic_set(0, 0, 0), [(-np.inf, np.inf)])
        self.assertEqual(quadratic_set(0, 2, -4), [(-np.inf, 2.)])

    def test_hac_lag_zero_intercept_matches_sample_standard_error(self):
        y = np.array([1., 3., 2., 8., 4.])
        beta, cov, _ = ols_hac(y, np.ones((len(y), 1)), lags=0)
        self.assertAlmostEqual(beta[0], y.mean())
        self.assertAlmostEqual(cov[0, 0], y.var(ddof=1)/len(y))

    def test_iv_recovers_noisy_stationary_process(self):
        rng = np.random.default_rng(2026)
        latent = np.zeros(20000)
        for i in range(1, len(latent)):
            latent[i] = .7*latent[i-1] + rng.normal()
        observed = latent + rng.normal(size=len(latent))
        phi_iv = iv_from_triplets(lag_triplets(observed))
        phi_ols = np.polyfit(observed[:-1], observed[1:], 1)[0]
        self.assertLess(abs(phi_iv-.7), .05)
        self.assertLess(phi_ols, phi_iv-.1)

    def test_anderson_rubin_contains_iv_estimate(self):
        rng = np.random.default_rng(4)
        L = np.zeros(120)
        for t in range(1, len(L)):
            L[t] = .8*L[t-1]+rng.normal(scale=.2)
        d = iv_diagnostic(L)
        self.assertTrue(any(lo <= d['phi_iv'] <= hi for lo, hi in d['confidence_set']))

    def test_panel_bootstrap_keeps_shared_shocks_synchronised(self):
        # Répliquer un duel identique ne doit pas réduire artificiellement son incertitude.
        L = np.random.default_rng(8).normal(size=60).cumsum()
        dates = [f'{2020+i//12}-{i%12+1:02d}' for i in range(len(L))]
        one = panel_bootstrap_iv([L], [dates], B=100)
        two = panel_bootstrap_iv([L, L], [dates, dates], B=100)
        np.testing.assert_allclose(one, two, atol=1e-12)
        self.assertAlmostEqual(pooled_iv([L]), pooled_iv([L, L]))

    def test_future_mutation_cannot_change_earlier_forecasts(self):
        rng = np.random.default_rng(3)
        s = expit(rng.normal(0, .1, 60).cumsum())
        months = np.arange(60)%12+1
        original = rolling_backtest(s, months)
        changed = s.copy(); changed[45:] = .99
        altered = rolling_backtest(changed, months)
        for a, b in zip(original, altered):
            if a['origin'] <= 45:
                self.assertAlmostEqual(a['prediction'], b['prediction'])
        scores = backtest_scores(original)
        for horizon in (1, 3, 6):
            self.assertEqual({r['n'] for r in scores if r['horizon'] == horizon}, {60-30-horizon+1})

    def test_finite_accumulation_derivative(self):
        for r in (.4, 1., 1.5):
            for share in (.2, .5, .8):
                rho = share/(1-share); c = rho**(1-r)
                for b in (.5, 5., 100.):
                    h = rho*1e-5
                    numerical = (etape_ratio(rho+h, r, b, c)-etape_ratio(rho-h, r, b, c))/(2*h)
                    self.assertAlmostEqual(numerical, persistance_locale(r, b, share), places=7)


if __name__ == '__main__':
    unittest.main()
