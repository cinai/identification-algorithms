# -*- coding: utf-8 -*-
import numpy as np
import time

#Función que filtra columnas de acuerdo a una lista de indices
#filter_features: matrix list -> matrix
def filter_features(vector,selected_features,features_dict):
    selected = []
    for i in range(len(selected_features)):
        selected.append(features_dict[selected_features[i]])
    return vector[:,selected]

def compare_vectors_with_neighbours_normalized(vector_a,vector_b,rois_a,rois_b,shared_rois,limit,min_shared,f_dist):
    a_matrix = np.ones((limit, limit)) * -1
    init_time = time.time()
    for i in range(limit):
        #print "Usuario ",i
        rois_abril = rois_a[i]
        neighbours = get_neighbours_index(rois_abril,shared_rois,i,min_shared)
        if len(neighbours) > 0:
            if len(neighbours) == 1:
                a_matrix[i,neighbours[0]] = 0
            else:
                a_sequence = vector_a[i,:]
                b_sequences = vector_b[neighbours,:]
                ab_sequences = np.vstack((a_sequence,b_sequences))
                counter = 0
                for neighbour in neighbours:
                    dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]))
                    a_matrix[i,neighbour] = -dist
                    counter += 1
    delta_time = time.time() - init_time
    print delta_time
    return a_matrix

def compare_vectors_with_neighbours_normalized_without_opt(vector_a,vector_b,rois_a,rois_b,shared_rois,limit,min_shared,f_dist):
    a_matrix = np.ones((limit, limit)) * -1
    init_time = time.time()
    for i in range(limit):
        #print "Usuario ",i
        rois_abril = rois_a[i]
        neighbours = get_neighbours_index(rois_abril,shared_rois,i,min_shared)
        if len(neighbours) > 0:
            a_sequence = vector_a[i,:]
            b_sequences = vector_b[neighbours,:]
            ab_sequences = np.vstack((a_sequence,b_sequences))
            counter = 0
            for neighbour in neighbours:
                dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]))
                a_matrix[i,neighbour] = -dist
                counter += 1
    delta_time = time.time() - init_time
    print delta_time
    return a_matrix

def get_n_correct(a_matrix,limit):
    identified_indexs = [] #almacena los indices de que secuencia fue seleccionada como match
    wrong_indexs = [] # almacena los indices de los que se clasificaron incorrectamente
    correct_indexs = [] # almacena los indices de los que se clasificaron correctamente
    selected_distance = [] # almacena la distancia de los seleccionados
    abstenidos = []
    n_identified = 0
    for i in range(limit):
        the_index = np.argmax(a_matrix[i,:])
        selected_distance.append(a_matrix[i,the_index])
        if a_matrix[i,the_index] == -1:
        	identified_indexs.append(-1)
        	abstenidos.append(i)
        elif(the_index!=i):
        	identified_indexs.append(the_index)
        	wrong_indexs.append(the_index)
        else:
        	identified_indexs.append(the_index)
        	correct_indexs.append(the_index)
        	n_identified += 1
    return [n_identified,selected_distance,identified_indexs,abstenidos]
#normalizar: [float] -> [float(0,1)]
#Normalizacion mayor menor
def normalizar_min_max(vector):
    a_max = np.max(vector)
    a_min = np.min(vector)
    if a_max == 0 and a_min == 0:
        return vector
    #if a_max == 0:
     #   a_max= a_min*0.0000001
    for i in range(len(vector)):
        vector[i] = (vector[i] - a_min)/a_max
    return vector    

#get_neighbours_index: np.matrix int -> np.array
#obtiene los vecinos del usuario "user",
#considerando como vecino a quien comparte dos ubicaciones
def get_neighbours_index(rois_a,shared_rois,user,min_shared):
    min_shared_x = min(len(rois_a),min_shared)
    neighbours = np.where(shared_rois[user] >= min_shared_x)
    return neighbours[0]