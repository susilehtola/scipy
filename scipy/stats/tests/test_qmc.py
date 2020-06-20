import copy
import numpy as np
from numpy.testing import (assert_allclose, assert_almost_equal, assert_,
                           assert_equal, assert_array_almost_equal,
                           assert_array_equal)
from pytest import raises as assert_raises

from scipy.stats import shapiro

from scipy.stats._sobol import _test_find_index
from scipy.stats import qmc


class TestUtils(object):
    def test_scale(self):
        space = [[0, 0], [1, 1], [0.5, 0.5]]
        corners = np.array([[-2, 0], [6, 5]])
        out = [[-2, 0], [6, 5], [2, 2.5]]

        scaled_space = qmc.scale(space, bounds=corners)

        assert_allclose(scaled_space, out)

        scaled_back_space = qmc.scale(scaled_space, bounds=corners, reverse=True)
        assert_allclose(scaled_back_space, space)


    def test_discrepancy(self):
        space_0 = [[0.1, 0.5], [0.2, 0.4], [0.3, 0.3], [0.4, 0.2], [0.5, 0.1]]
        space_1 = [[1, 3], [2, 6], [3, 2], [4, 5], [5, 1], [6, 4]]
        space_2 = [[1, 5], [2, 4], [3, 3], [4, 2], [5, 1], [6, 6]]

        corners = np.array([[0.5, 0.5], [6.5, 6.5]])

        assert_allclose(qmc.discrepancy(space_0), 0.1353, atol=1e-4)

        # From Fang et al. Design and modeling for computer experiments, 2006
        assert_allclose(qmc.discrepancy(space_1, corners), 0.0081, atol=1e-4)
        assert_allclose(qmc.discrepancy(space_2, corners), 0.0105, atol=1e-4)

    def test_update_discrepancy(self):
        space_0 = [[0.1, 0.5], [0.2, 0.4], [0.3, 0.3], [0.4, 0.2], [0.5, 0.1]]
        space_1 = [[1, 3], [2, 6], [3, 2], [4, 5], [5, 1], [6, 4]]

        # without bounds
        disc_init = qmc.discrepancy(space_0[:-1], iterative=True)
        disc_iter = qmc._update_discrepancy(space_0[-1], space_0[:-1],
                                            disc_init)

        assert_allclose(disc_iter, 0.1353, atol=1e-4)

        # with bounds
        corners = np.array([[0.5, 0.5], [6.5, 6.5]])

        disc_init = qmc.discrepancy(space_1[:-1], corners, iterative=True)
        disc_iter = qmc._update_discrepancy(space_1[-1], space_1[:-1],
                                            disc_init, bounds=corners)

        assert_allclose(disc_iter, 0.0081, atol=1e-4)

    def test_perm_discrepancy(self):
        doe_init = np.array([[1, 3], [2, 6], [3, 2], [4, 5], [5, 1], [6, 4]])
        corners = np.array([[0.5, 0.5], [6.5, 6.5]])
        disc_init = qmc.discrepancy(doe_init, corners)

        row_1, row_2, col = 5, 2, 1

        doe = copy.deepcopy(doe_init)
        doe[row_1, col], doe[row_2, col] = doe[row_2, col], doe[row_1, col]

        disc_valid = qmc.discrepancy(doe, corners)
        disc_perm = qmc._perturb_discrepancy(doe_init, row_1, row_2, col,
                                             disc_init, corners)

        assert_allclose(disc_valid, disc_perm)

    def test_n_primes(self):
        n_primes = qmc.n_primes(10)
        assert n_primes[-1] == 29

        n_primes = qmc.n_primes(168)
        assert n_primes[-1] == 997

        n_primes = qmc.n_primes(350)
        assert n_primes[-1] == 2357

    def test_primes(self):
        primes = qmc.primes_from_2_to(50)
        out = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        assert_allclose(primes, out)


class TestQMC(object):
    def test_van_der_corput(self):
        sample = qmc.van_der_corput(10)
        out = [0., 0.5, 0.25, 0.75, 0.125, 0.625, 0.375, 0.875, 0.0625, 0.5625]
        assert_almost_equal(sample, out)

        sample = qmc.van_der_corput(5, start_index=3)
        out = [0.75, 0.125, 0.625, 0.375, 0.875]
        assert_almost_equal(sample, out)

    def test_halton(self):
        # without bounds
        engine = qmc.Halton(k_vars=2)
        sample = engine.random(n_samples=5)

        out = np.array([[1 / 2, 1 / 3], [1 / 4, 2 / 3], [3 / 4, 1 / 9], [1 / 8, 4 / 9], [5 / 8, 7 / 9]])
        assert_almost_equal(sample, out, decimal=1)

        assert engine.num_generated == 5

        # with bounds
        corners = np.array([[0, 2], [10, 5]])
        sample = qmc.scale(sample, bounds=corners)

        out = np.array([[5., 3.], [2.5, 4.], [7.5, 2.3], [1.25, 3.3], [6.25, 4.3]])
        assert_almost_equal(sample, out, decimal=1)

        # continuing
        engine = qmc.Halton(k_vars=2)
        engine.fast_forward(2)
        sample = engine.random(n_samples=3)
        sample = qmc.scale(sample, bounds=corners)

        out = np.array([[7.5, 2.3], [1.25, 3.3], [6.25, 4.3]])
        assert_almost_equal(sample, out, decimal=1)


class TestLHS(object):
    def test_lhs(self):
        np.random.seed(123456)

        corners = np.array([[0, 2], [10, 5]])

        lhs = qmc.LatinHypercube(k_vars=2)
        sample = lhs.random(n_samples=5)
        sample = qmc.scale(sample, bounds=corners)
        out = np.array([[5.7, 3.2], [5.5, 3.9], [5.2, 3.6],
                        [5.1, 3.3], [5.8, 4.1]])
        assert_almost_equal(sample, out, decimal=1)

        lhs = qmc.LatinHypercube(k_vars=2, centered=True)
        sample = lhs.random(n_samples=5)
        out = np.array([[0.1, 0.5], [0.3, 0.1], [0.7, 0.1],
                        [0.1, 0.1], [0.3, 0.7]])
        assert_almost_equal(sample, out, decimal=1)

    def test_orthogonal_lhs(self):
        np.random.seed(123456)

        corners = np.array([[0, 2], [10, 5]])

        olhs = qmc.OrthogonalLatinHypercube(k_vars=2)
        sample = olhs.random(n_samples=5)
        sample = qmc.scale(sample, bounds=corners)
        out = np.array([[3.933, 2.670], [7.794, 4.031], [4.520, 2.129],
                        [0.253, 4.976], [8.753, 3.249]])
        assert_almost_equal(sample, out, decimal=1)

        # Checking independency of the random numbers generated
        n_samples = 500
        sample = olhs.random(n_samples=n_samples)
        min_b = 50  # number of bins
        bins = np.linspace(0, 1, min(min_b, n_samples) + 1)
        hist = np.histogram(sample[:, 0], bins=bins)
        out = np.array([n_samples / min_b] * min_b)
        assert_equal(hist[0], out)

        hist = np.histogram(sample[:, 1], bins=bins)
        assert_equal(hist[0], out)

    def test_optimal_design(self):
        seed = 123456

        olhs = qmc.OrthogonalLatinHypercube(k_vars=2, seed=seed)
        sample_ref = olhs.random(n_samples=20)
        disc_ref = qmc.discrepancy(sample_ref)

        optimal_1 = qmc.OptimalDesign(k_vars=2, start_design=sample_ref, seed=seed)
        sample_1 = optimal_1.random(n_samples=20)
        disc_1 = qmc.discrepancy(sample_1)

        assert disc_1 < disc_ref

        optimal_ = qmc.OptimalDesign(k_vars=2, seed=seed)
        sample_ = optimal_.random(n_samples=20)
        disc_ = qmc.discrepancy(sample_)

        assert disc_ < disc_ref

        optimal_2 = qmc.OptimalDesign(k_vars=2, start_design=sample_ref, niter=2, seed=seed)
        sample_2 = optimal_2.random(n_samples=20)
        disc_2 = qmc.discrepancy(sample_2)
        assert disc_2 < disc_1

        # resample is like doing another iteration
        sample_1 = optimal_1.random(n_samples=20)
        assert_allclose(sample_1, sample_2)

        optimal_3 = qmc.OptimalDesign(k_vars=2, start_design=sample_ref, force=True)
        sample_3 = optimal_3.random(n_samples=20)
        disc_3 = qmc.discrepancy(sample_3)
        assert disc_3 < disc_ref

        # no optimization
        optimal_4 = qmc.OptimalDesign(k_vars=2, start_design=sample_ref,
                                      optimization=False, niter=100, seed=seed)
        sample_4 = optimal_4.random(n_samples=20)
        disc_4 = qmc.discrepancy(sample_4)

        assert disc_4 < disc_ref


class TestMultinomialQMC:
    def test_MultinomialNegativePs(self):
        p = np.array([0.12, 0.26, -0.05, 0.35, 0.22])
        assert_raises(ValueError, qmc.multinomial_qmc, 10, p)

    def test_MultinomialSumOfPTooLarge(self):
        p = np.array([0.12, 0.26, 0.1, 0.35, 0.22])
        assert_raises(ValueError, qmc.multinomial_qmc, 10, p)

    def test_MultinomialBasicDraw(self):
        p = np.array([0.12, 0.26, 0.05, 0.35, 0.22])
        expected = np.array([12, 25, 6, 34, 23])
        assert_array_equal(qmc.multinomial_qmc(100, p, seed=12345), expected)

    def test_MultinomialDistribution(self):
        p = np.array([0.12, 0.26, 0.05, 0.35, 0.22])
        draws = qmc.multinomial_qmc(10000, p, seed=12345)
        assert_array_almost_equal(draws / np.sum(draws), p, decimal=4)

    def test_FindIndex(self):
        p_cumulative = np.array([0.1, 0.4, 0.45, 0.6, 0.75, 0.9, 0.99, 1.0])
        size = len(p_cumulative)
        assert_equal(_test_find_index(p_cumulative, size, 0.0), 0)
        assert_equal(_test_find_index(p_cumulative, size, 0.4), 2)
        assert_equal(_test_find_index(p_cumulative, size, 0.44999), 2)
        assert_equal(_test_find_index(p_cumulative, size, 0.45001), 3)
        assert_equal(_test_find_index(p_cumulative, size, 1.0), size - 1)

    def test_other_engine(self):
        # same as test_MultinomialBasicDraw with different engine
        p = np.array([0.12, 0.26, 0.05, 0.35, 0.22])
        expected = np.array([12, 25, 6, 34, 23])
        engine = qmc.Sobol(1, scramble=True, seed=12345)
        assert_array_equal(qmc.multinomial_qmc(100, p, engine=engine, seed=12345),
                           expected)


class TestNormalQMC:
    def test_NormalQMC(self):
        # d = 1
        engine = qmc.NormalQMC(k_vars=1)
        samples = engine.random()
        assert_equal(samples.shape, (1, 1))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 1))
        # d = 2
        engine = qmc.NormalQMC(k_vars=2)
        samples = engine.random()
        assert_equal(samples.shape, (1, 2))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 2))

    def test_NormalQMCInvTransform(self):
        # d = 1
        engine = qmc.NormalQMC(k_vars=1, inv_transform=True)
        samples = engine.random()
        assert_equal(samples.shape, (1, 1))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 1))
        # d = 2
        engine = qmc.NormalQMC(k_vars=2, inv_transform=True)
        samples = engine.random()
        assert_equal(samples.shape, (1, 2))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 2))

    def test_other_engine(self):
        engine = qmc.NormalQMC(k_vars=2, engine=qmc.Sobol(k_vars=2, scramble=True), inv_transform=True)
        samples = engine.random()
        assert_equal(samples.shape, (1, 2))

    def test_NormalQMCSeeded(self):
        # test even dimension
        engine = qmc.NormalQMC(k_vars=2, seed=12345)
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [[-0.63099602, -1.32950772], [0.29625805, 1.86425618]]
        )
        assert_array_almost_equal(samples, samples_expected)
        # test odd dimension
        engine = qmc.NormalQMC(k_vars=3, seed=12345)
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [
                [1.83169884, -1.40473647, 0.24334828],
                [0.36596099, 1.2987395, -0.330971],
            ]
        )
        assert_array_almost_equal(samples, samples_expected)

    def test_NormalQMCSeededInvTransform(self):
        # test even dimension
        engine = qmc.NormalQMC(k_vars=2, seed=12345, inv_transform=True)
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [[-0.41622922, 0.46622792], [-0.96063897, -0.75568963]]
        )
        assert_array_almost_equal(samples, samples_expected)
        # test odd dimension
        engine = qmc.NormalQMC(k_vars=3, seed=12345, inv_transform=True)
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [
                [-1.40525266, 1.37652443, -0.8519666],
                [-0.166497, -2.3153681, 0.840378],
            ]
        )
        assert_array_almost_equal(samples, samples_expected)

    def test_NormalQMCShapiro(self):
        engine = qmc.NormalQMC(k_vars=2, seed=12345)
        samples = engine.random(n_samples=250)
        assert_(all(np.abs(samples.mean(axis=0)) < 1e-2))
        assert_(all(np.abs(samples.std(axis=0) - 1) < 1e-2))
        # perform Shapiro-Wilk test for normality
        for i in (0, 1):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.9)
        # make sure samples are uncorrelated
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1]) < 1e-2)

    def test_NormalQMCShapiroInvTransform(self):
        engine = qmc.NormalQMC(k_vars=2, seed=12345, inv_transform=True)
        samples = engine.random(n_samples=250)
        assert_(all(np.abs(samples.mean(axis=0)) < 1e-2))
        assert_(all(np.abs(samples.std(axis=0) - 1) < 1e-2))
        # perform Shapiro-Wilk test for normality
        for i in (0, 1):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.9)
        # make sure samples are uncorrelated
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1]) < 1e-2)


class TestMultivariateNormalQMC:
    def test_MultivariateNormalQMCNonPSD(self):
        # try with non-psd, non-pd cov and expect an assertion error
        assert_raises(
            ValueError, qmc.MultivariateNormalQMC, [0, 0], [[1, 2], [2, 1]]
        )

    def test_MultivariateNormalQMCNonPD(self):
        # try with non-pd but psd cov; should work
        engine = qmc.MultivariateNormalQMC(
            [0, 0, 0], [[1, 0, 1], [0, 1, 1], [1, 1, 2]]
        )
        assert_(engine._corr_matrix is not None)

    def test_MultivariateNormalQMCSymmetric(self):
        # try with non-symmetric cov and expect an error
        assert_raises(
            ValueError, qmc.MultivariateNormalQMC, [0, 0], [[1, 0], [2, 1]]
        )

    def test_MultivariateNormalQMCCov(self):
        # non square covariance matrix
        assert_raises(
            ValueError, qmc.MultivariateNormalQMC, [0, 0], [[1], [2, 1]]
        )

    def test_MultivariateNormalQMCDim(self):
        # incompatible dimension of mean/cov
        assert_raises(
            ValueError, qmc.MultivariateNormalQMC, [0], [[1, 0], [0, 1]]
        )

    def test_MultivariateNormalQMC(self):
        # d = 1 scalar
        engine = qmc.MultivariateNormalQMC(mean=0, cov=5)
        samples = engine.random()
        assert_equal(samples.shape, (1, 1))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 1))

        # d = 2 list
        engine = qmc.MultivariateNormalQMC(mean=[0, 1], cov=[[1, 0], [0, 1]])
        samples = engine.random()
        assert_equal(samples.shape, (1, 2))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 2))

        # d = 3 np.array
        mean = np.array([0, 1, 2])
        cov = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        engine = qmc.MultivariateNormalQMC(mean, cov)
        samples = engine.random()
        assert_equal(samples.shape, (1, 3))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 3))

    def test_MultivariateNormalQMCInvTransform(self):
        # d = 1 scalar
        engine = qmc.MultivariateNormalQMC(mean=0, cov=5, inv_transform=True)
        samples = engine.random()
        assert_equal(samples.shape, (1, 1))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 1))

        # d = 2 list
        engine = qmc.MultivariateNormalQMC(
            mean=[0, 1], cov=[[1, 0], [0, 1]], inv_transform=True
        )
        samples = engine.random()
        assert_equal(samples.shape, (1, 2))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 2))

        # d = 3 np.array
        mean = np.array([0, 1, 2])
        cov = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        engine = qmc.MultivariateNormalQMC(mean, cov, inv_transform=True)
        samples = engine.random()
        assert_equal(samples.shape, (1, 3))
        samples = engine.random(n_samples=5)
        assert_equal(samples.shape, (5, 3))

    def test_MultivariateNormalQMCSeeded(self):
        # test even dimension
        np.random.seed(54321)
        a = np.random.randn(2, 2)
        A = a @ a.transpose() + np.diag(np.random.rand(2))
        engine = qmc.MultivariateNormalQMC(np.array([0, 0]), A, seed=12345)
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [[-0.67595995, -2.27437872], [0.317369, 2.66203577]]
        )
        assert_array_almost_equal(samples, samples_expected)

        # test odd dimension
        np.random.seed(54321)
        a = np.random.randn(3, 3)
        A = a @ a.transpose() + np.diag(np.random.rand(3))
        engine = qmc.MultivariateNormalQMC(np.array([0, 0, 0]), A, seed=12345)
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [
                [2.05178452, -6.35744194, 0.67944512],
                [0.40993262, 2.60517697, -0.43475],
            ]
        )
        assert_array_almost_equal(samples, samples_expected)

    def test_MultivariateNormalQMCSeededInvTransform(self):
        # test even dimension
        np.random.seed(54321)
        a = np.random.randn(2, 2)
        A = a @ a.transpose() + np.diag(np.random.rand(2))
        engine = qmc.MultivariateNormalQMC(
            np.array([0, 0]), A, seed=12345, inv_transform=True
        )
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [[-0.44588916, 0.22657776], [-1.02909281, -1.83193033]]
        )
        assert_array_almost_equal(samples, samples_expected)

        # test odd dimension
        np.random.seed(54321)
        a = np.random.randn(3, 3)
        A = a @ a.transpose() + np.diag(np.random.rand(3))
        engine = qmc.MultivariateNormalQMC(
            np.array([0, 0, 0]), A, seed=12345, inv_transform=True
        )
        samples = engine.random(n_samples=2)
        samples_expected = np.array(
            [
                [-1.5740992, 5.61057598, -1.28218525],
                [-0.18650226, -5.41662685, 1.12366],
            ]
        )
        assert_array_almost_equal(samples, samples_expected)

    def test_MultivariateNormalQMCShapiro(self):
        # test the standard case
        engine = qmc.MultivariateNormalQMC(
            mean=[0, 0], cov=[[1, 0], [0, 1]], seed=12345
        )
        samples = engine.random(n_samples=250)
        assert_(all(np.abs(samples.mean(axis=0)) < 1e-2))
        assert_(all(np.abs(samples.std(axis=0) - 1) < 1e-2))
        # perform Shapiro-Wilk test for normality
        for i in (0, 1):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.9)
        # make sure samples are uncorrelated
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1]) < 1e-2)

        # test the correlated, non-zero mean case
        engine = qmc.MultivariateNormalQMC(
            mean=[1.0, 2.0], cov=[[1.5, 0.5], [0.5, 1.5]], seed=12345
        )
        samples = engine.random(n_samples=250)
        assert_(all(np.abs(samples.mean(axis=0) - [1, 2]) < 1e-2))
        assert_(all(np.abs(samples.std(axis=0) - np.sqrt(1.5)) < 1e-2))
        # perform Shapiro-Wilk test for normality
        for i in (0, 1):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.9)
        # check covariance
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1] - 0.5) < 1e-2)

    def test_MultivariateNormalQMCShapiroInvTransform(self):
        # test the standard case
        engine = qmc.MultivariateNormalQMC(
            mean=[0, 0], cov=[[1, 0], [0, 1]], seed=12345, inv_transform=True
        )
        samples = engine.random(n_samples=250)
        assert_(all(np.abs(samples.mean(axis=0)) < 1e-2))
        assert_(all(np.abs(samples.std(axis=0) - 1) < 1e-2))
        # perform Shapiro-Wilk test for normality
        for i in (0, 1):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.9)
        # make sure samples are uncorrelated
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1]) < 1e-2)

        # test the correlated, non-zero mean case
        engine = qmc.MultivariateNormalQMC(
            mean=[1.0, 2.0],
            cov=[[1.5, 0.5], [0.5, 1.5]],
            seed=12345,
            inv_transform=True,
        )
        samples = engine.random(n_samples=250)
        assert_(all(np.abs(samples.mean(axis=0) - [1, 2]) < 1e-2))
        assert_(all(np.abs(samples.std(axis=0) - np.sqrt(1.5)) < 1e-2))
        # perform Shapiro-Wilk test for normality
        for i in (0, 1):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.9)
        # check covariance
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1] - 0.5) < 1e-2)

    def test_MultivariateNormalQMCDegenerate(self):
        # X, Y iid standard Normal and Z = X + Y, random vector (X, Y, Z)
        engine = qmc.MultivariateNormalQMC(
            mean=[0.0, 0.0, 0.0],
            cov=[[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [1.0, 1.0, 2.0]],
            seed=12345,
        )
        samples = engine.random(n_samples=2000)
        assert_(all(np.abs(samples.mean(axis=0)) < 1e-2))
        assert_(np.abs(np.std(samples[:, 0]) - 1) < 1e-2)
        assert_(np.abs(np.std(samples[:, 1]) - 1) < 1e-2)
        assert_(np.abs(np.std(samples[:, 2]) - np.sqrt(2)) < 1e-2)
        for i in (0, 1, 2):
            _, pval = shapiro(samples[:, i])
            assert_(pval > 0.8)
        cov = np.cov(samples.transpose())
        assert_(np.abs(cov[0, 1]) < 1e-2)
        assert_(np.abs(cov[0, 2] - 1) < 1e-2)
        # check to see if X + Y = Z almost exactly
        assert_(
            all(np.abs(samples[:, 0] + samples[:, 1] - samples[:, 2]) < 1e-5)
        )
