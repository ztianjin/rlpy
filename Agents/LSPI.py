######################################################
# Developed by Alborz Geramiard Nov 19th 2012 at MIT #
######################################################
# Least-Squares Policy Iteration [Lagoudakis and Parr 2003]
# This version recalculates the policy every <sample_window>. Samples are obtained using the recent version of the policy  
from OnlineAgent import *
class LSPI(Agent):
    lspi_iterations = 0         # Number of LSPI iterations
    sample_window   = 0         # Number of samples to be used to calculate the LSTD solution
    samples_count   = 0         # Counter for the sample count
    epsilon         = 0         # Minimum l_2 change required to continue iterations in LSPI
    #Store Data in separate matrixes
    data_s          = []        # 
    data_a          = []        # 
    data_r          = []        #
    data_ns         = []        # 
    data_na         = []        # 
        
    def __init__(self,representation,policy,domain, lspi_iterations = 5, sample_window = 100, epsilon = 1e-3):
        self.samples_count      = 0
        self.sample_window      = sample_window
        self.epsilon            = epsilon
        self.lspi_iterations    = lspi_iterations
        self.phi_sa_size        = domain.actions_num * representation.features_num
        self.data_s             = zeros((sample_window, domain.state_space_dims))
        self.data_ns            = zeros((sample_window, domain.state_space_dims))
        self.data_a             = zeros(sample_window,dtype=uint16)
        self.data_na            = zeros(sample_window,dtype=uint16)
        self.data_r             = zeros(sample_window)
        super(LSPI, self).__init__(representation, policy, domain)
    def learn(self,s,a,r,ns,na,terminal):
        
        self.storeData(s,a,r,ns,na)        
        
        if self.samples_count == self.sample_window: #zero based hence the -1

            # Run LSTD for first solution
            A,b, all_phi_s, all_phi_s_a, all_phi_ns = self.LSTD()
            # Run Policy Iteration to change a_prime and recalculate theta
            self.policyIteration()
    def policyIteration(self,all_phi_s_a,all_phi_ns):
            #Update the policy by recalculating A based on new na
            #Returns the TD error for each sample based on the latest weights and na
            phi_sa_size     = self.domain.actions_num*self.representation.features_num
            gamma           = self.domain.gamma
            td_errors       = empty((self.sample_window)) # holds the TD_errors for all samples

            #Begin updating the policy in LSPI loop
            weight_diff     = self.epsilon + 1 # So that the loop starts
            lspi_iteration  = 0
            while lspi_iteration < self.lspi_iterations and weight_diff > self.epsilon:
                A = sp.coo_matrix((phi_sa_size,phi_sa_size))
                for i in range(self.sample_window):
                    phi_s_a         = all_phi_s_a[i,:]
                    phi_ns          = all_phi_ns[i,:]
                    new_na          = self.representation.bestAction(s,phi_ns)
                    phi_ns_new_na   = self.representation.phi_sa(s,new_na,phi_ns)
                    d               = phi_s_a-gamma*phi_ns_new_na
                    A               = A + outer(phi_s_a,d) 
                    td_errors[i]    = self.data_r[i]+dot(-d,self.representation.theta)
                #Calculate theta
                new_theta                   = solveLinear(sp.csc_matrix(A),b)
                weight_diff                 = linalg.norm(self.representation.theta - new_theta)
                if weight_diff > self.epsilon: self.representation.theta   = new_theta
                print "%d: L2_norm of weight difference = %0.3f" % (lspi_iteration,weight_diff)
                lspi_iteration +=1
            return td_errors
    def LSTD(self): 
        self.samples_count  = 0
        # Calculate the A and b matrixes in LSTD
        phi_sa_size     = self.domain.actions_num*self.representation.features_num
        A               = sp.coo_matrix((phi_sa_size,phi_sa_size))
        b               = zeros(phi_sa_size)
        all_phi_s       = zeros((self.sample_window,self.representation.features_num)) #phi_s will be saved for batch iFDD
        all_phi_s_a     = zeros((self.sample_window,phi_sa_size)) #phi_sa will be fixed during iterations
        all_phi_ns      = zeros((self.sample_window,self.representation.features_num)) #phi_ns_na will change according to na so we only cache the phi_na which remains the same
        
        #print "Making A,b"
        gamma               = self.representation.domain.gamma
        for i in range(self.sample_window):
            s                   = self.data_s[i]
            ns                  = self.data_ns[i]
            a                   = self.data_a[i]
            na                  = self.data_na[i]
            r                   = self.data_r[i]
            phi_s               = self.representation.phi(s)
            phi_s_a             = self.representation.phi_sa(s,a,phi_s)
            phi_ns              = self.representation.phi(ns)
            phi_ns_na           = self.representation.phi_sa(ns,na,phi_ns)
            all_phi_s[i,:]      = phi_s
            all_phi_s_a[i,:]    = phi_s_a
            all_phi_ns[i,:]     = phi_ns
            d                   = phi_s_a-gamma*phi_ns_na
            A                   = A + outer(phi_s_a,d) 
            b                   = b + r*phi_s_a

        #Calculate theta
        self.representation.theta = solveLinear(sp.csc_matrix(A),b)
        return A,b, all_phi_s, all_phi_s_a, all_phi_ns 
    def storeData(self,s,a,r,ns,na):
        self.data_s[self.samples_count,:]   = s
        self.data_a[self.samples_count]   = a
        self.data_r[self.samples_count]   = r
        self.data_ns[self.samples_count,:]  = ns
        self.data_na[self.samples_count]  = na
        self.samples_count                  += 1