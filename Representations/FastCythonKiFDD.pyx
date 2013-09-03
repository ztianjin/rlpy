from libcpp.vector cimport vector

from libcpp.string cimport string as stlstring
from libcpp cimport bool
from libcpp.set cimport set as sett
cimport numpy as np
import numpy as np
cimport cython
ctypedef unsigned int uint

cdef extern from "FastKiFDD.h":
    cdef double gaussian_kernel(vector[double] s1, vector[double] s2, vector[unsigned int] dim, vector[double] widths)
    cdef double linf_triangle_kernel(vector[double] s1, vector[double] s2, vector[unsigned int] dim, vector[double] widths)
    cdef cppclass FastKiFDD:
        FastKiFDD(double, double, stlstring, vector[double], int, double, unsigned int)
        vector[double] phi(vector[double])
        unsigned int discover(vector[double] s, unsigned int a, double td_error, vector[double] previous_phi)
        bool verbose
        int features_num
        double activation_threshold
        double discovery_threshold
        double max_neighbor_similarity
        int sparsification
        vector[sett[uint]] base_ids

cdef class FastCythonKiFDD:

    cdef FastKiFDD *thisptr      # hold a C++ instance which we're wrapping
    def __cinit__(self, domain, kernel, active_threshold, discover_threshold,
                 logger=None, kernel_args=[], normalization=True, sparsify=True,
                 max_active_base_feat=2, max_base_feat_sim=0.7):

        cdef vector[double] kw
        for k in kernel_args[0]:
            kw.push_back(k)
        cdef stlstring kernel_string = kernel.__name__
        self.thisptr = new FastKiFDD(active_threshold, discover_threshold, kernel_string,
                                     kw, sparsify, max_base_feat_sim, max_active_base_feat)

    def __dealloc__(self):
        del self.thisptr

    def phi_nonTerminal(self, np.ndarray[np.double_t, ndim=1] s):
        cdef vector[double] sv
        for se in s:
            sv.push_back(se)
        cdef vector[double] fv
        fv = self.thisptr.phi(sv)

        return np.array(list(fv))

    @property
    def activation_threshold(self):
        return self.thisptr.activation_threshold

    @property
    def discovery_threshold(self):
        return self.thisptr.discovery_threshold

    @property
    def max_neighbor_similarity(self):
        return self.thisptr.max_neighbor_similarity

    @property
    def sparsification(self):
        return self.thisptr.sparsification

    @property
    def verbose(self):
        return self.thisptr.verbose

    @verbose.setter
    def set_verbose(self, bool v):
        self.thisptr.verbose = v

    def discover(self,  np.ndarray[np.double_t, ndim=1] s, unsigned int a, double td_error, np.ndarray phi):
        cdef vector[double] sv
        for se in s:
            sv.push_back(se)
        cdef vector[double] prev_phi
        for p in phi:
            prev_phi.push_back(p)
        return self.thisptr.discover(sv, a, td_error, prev_phi)

