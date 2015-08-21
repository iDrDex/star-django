cimport numpy as np
import numpy as np

from libc.math cimport sqrt


cdef double NaN = float('nan')


cpdef _get_TE_se(double[:] caseSigma, long[:] caseCount,
                 double[:] controlSigma, long[:] controlCount):
    cdef np.ndarray[double] res = np.zeros_like(caseSigma)
    cdef Py_ssize_t i, n = len(caseSigma)
    for i in range(n):
        # Studies with non-positive variance get zero weight in meta-analysis
        if caseSigma[i] <= 0  or controlSigma[i] <= 0:
            res[i] = NaN
        else:
            # MD method
            res[i] = sqrt(caseSigma[i] ** 2 / caseCount[i]
                          + controlSigma[i] ** 2 / controlCount[i])
    return res
