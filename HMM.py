import numpy as np
from hmmlearn import hmm

def hidden_markov(variables, length_list, observation_num):
    
    hidden_state_num = 3
    start_probability, transition_probability, emission_probability = init_probability(hidden_state_num, observation_num)
    
    model = hmm.MultinomialHMM(n_components=3, n_iter = 50, verbose = True)
    model.startprob_ = start_probability
    model.transmat_ = transition_probability
    model.emissionprob_ = emission_probability
    
    X = convert(variables)
    model = model.fit(np.atleast_2d(X).T, length_list)
    
    output_model(model)
#     print(model)
#     print(model.startprob_)
#     print(model.transmat_)
#     print(model.emissionprob_)

def init_probability(hidden_state_num, observation_num):
    start_p = 1/hidden_state_num
    trans_p = 1/hidden_state_num
    emiss_p = 1/observation_num
    
    start_arr = np.empty((1, hidden_state_num))
    start_arr[:] = start_p
    trans_arr = np.empty((hidden_state_num, hidden_state_num))
    trans_arr[:] = trans_p
    emiss_arr = np.empty((hidden_state_num, observation_num))
    emiss_arr[:] = emiss_p
    
    return start_arr, trans_arr, emiss_arr
    
def convert(variables):
    arr = []
    for l in variables:
        arr.append(np.array(l))
    X = np.concatenate(np.array(arr))
    return X

def output_model(m):   
    file_path = 'D:/Data/PSAA/'
    file = open(file_path + 'hmm_attrs.csv', 'w')
    file.write('startprob_:'+'\n')
    file.write(str(m.startprob_))
    file.write('\n')
    file.write('transmat_:'+'\n')
    file.write(str(m.transmat_))
    file.write('\n')
    file.write('emissprob_:'+'\n')
    file.write(str(m.emissionprob_))
    file.close()