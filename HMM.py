import numpy as np
from hmmlearn import hmm

def hidden_markov(variables, length_list, observation_num):
    
    hidden_state_num = 4
    start_probability, transition_probability, emission_probability = init_probability(hidden_state_num, observation_num)
    
    model = hmm.MultinomialHMM(n_components=hidden_state_num, n_iter = 50, verbose = True)
    model.startprob_ = start_probability
    model.transmat_ = transition_probability
    model.emissionprob_ = emission_probability
    
    X = convert(variables)
    model = model.fit(np.atleast_2d(X).T, length_list)
    
    emissionprob_sorted, emiss_seq = sort_emission_prob(model.emissionprob_)
    return model.startprob_, model.transmat_, emissionprob_sorted, emiss_seq
    #output_model(model)
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
    #print(start_arr)
    trans_arr = np.empty((hidden_state_num, hidden_state_num))
    trans_arr[:] = trans_p
    #print(trans_arr)
    emiss_arr = np.empty((hidden_state_num, observation_num))
    emiss_arr[:] = emiss_p
    #print(emiss_arr)
    
    return start_arr, trans_arr, emiss_arr
    
def convert(variables):
    arr = []
    for l in variables:
        arr.append(np.array(l))
    X = np.concatenate(np.array(arr))
    return X

def sort_emission_prob(emissionprob):
    #ascending
#     print(emissionprob)
    index_sorted = emissionprob.argsort()
    emissprob_sorted = np.sort(emissionprob)
#     index_sorted = np.argsort(emissionprob)[::-1]
#     print(index_sorted)
#     print(emissprob_sorted)
    return emissprob_sorted, index_sorted

def output_model(startprob, transmat, emissionprob, emissseq):   
    file_path = 'D:/Data/PSAA/'
    file = open(file_path + 'hmm_attrs3.csv', 'w')
    file.write('startprob:'+'\n')
    file.write(str(startprob))
    file.write('\n')
    file.write('transmat:'+'\n')
    file.write(str(transmat))
    file.write('\n')
    file.write('emissprob:'+'\n')
    file.write(str(emissionprob))
    file.write('\n')
    file.write('emissseq:'+'\n')
    file.write(str(emissseq))
    file.close()