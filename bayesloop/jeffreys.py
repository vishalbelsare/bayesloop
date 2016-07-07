#!/usr/bin/env python
"""
This file provides a single function that uses SymPy to determine the Jeffreys prior of an arbitrary probability
distribution defined within SymPy.
"""

import numpy as np
import sympy.abc as abc
from sympy.stats import density
from sympy import Symbol, Matrix, simplify, diff, integrate, summation, lambdify
from sympy import ln, sqrt


def getJeffreysPrior(rv):
    """
    Uses SymPy to determine the Jeffreys prior of a random variable analytically.

    Parameters:
        rv - SymPy RandomSymbol, corresponding to a probability distribution

    Returns:
        List, containing Jeffreys prior in symbolic form and corresponding lambda function

    Example:
        rate = Symbol('rate', positive=True)
        rv = stats.Exponential('exponential', rate)
        print getJeffreysPrior(rv)

        >>> (1/rate, <function <lambda> at 0x0000000007F79AC8>)
    """

    # get support of random variable
    support = rv._sorted_args[0].distribution.set

    # get list of free parameters
    parameters = list(rv._sorted_args[0].distribution.free_symbols)
    x = abc.x

    # symbolic probability density function
    symPDF = density(rv)(x)

    # compute Fisher information matrix
    dim = len(parameters)
    G = Matrix.zeros(dim, dim)

    func = summation if support.is_iterable else integrate
    for i in range(0, dim):
        for j in range(0, dim):
            G[i, j] = func(simplify(symPDF *
                                    diff(ln(symPDF), parameters[i]) *
                                    diff(ln(symPDF), parameters[j])),
                           (x, support.inf, support.sup))

    # symbolic Jeffreys prior
    symJeff = simplify(sqrt(G.det()))

    # return symbolic Jeffreys prior and corresponding lambda function
    return symJeff, lambdify(parameters, symJeff, 'numpy')


def computeJeffreysPriorAR1(study):
    """
    This function encodes the Jeffreys prior for the AR1 process as derived by Harald Uhlig in the work "On Jeffreys
    prior when using the exact likelihood function." (Econometric Theory 10 (1994): 633-633. Equation 31). Note that
    only the case of abs(r) < 1 (stationary process) is implemented at the moment.

    Parameters:
        study - Instance of the Study class that this prior is added to
    """
    if str(study.observationModel) == 'Autoregressive process of first order (AR1)':
        r, s = study.grid
    elif str(study.observationModel) == 'Scaled autoregressive process of first order (AR1)':
        r, s = study.grid
        s = s*np.sqrt(1 - r**2.)
    else:
        print '! Jeffreys prior for autoregressive process can only be used with AR1 and ScaledAR1 models.'
        return

    # if abs(rho) >= 1., flat prior is returned
    if np.any(np.abs(r) >= 1.):
        print '! Jeffreys prior for auto-regressive process is only implemented for stationary processes.'
        print '  Values abs(r) >= 1 are not allowed for this implementation of the prior.'
        print '  Will set flat prior instead.'
        flat = np.ones_like(r)
        flat /= np.sum(flat)
        return flat

    if len(study.rawData) == 0:
        print '! Data must be loaded before computing the Jeffreys prior for the autoregressive process.'
        return

    d0 = study.rawData[0]  # first observation is accounted for in the prior
    n = len(study.rawData)  # number of data points

    prior = (1/s**2.)*np.exp(-d0**2.*(1-r**2.)/(2*s**2.))*(4*(r**2.)/(1-r**2.)+2*(n+1))**.5
    prior /= np.sum(prior)
    return prior
