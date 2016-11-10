# -*- coding: utf-8 -*-
import numpy as np
import time
from geopy.distance import vincenty
from auxiliar_functions import *

#get_neighbours_index: np.matrix int -> np.array
#obtiene los vecinos del usuario "user",
#considerando como vecino a quien comparte dos ubicaciones
def get_neighbours_index(rois_a,shared_rois,user,min_shared):
    min_shared_x = min(len(rois_a),min_shared)
    neighbours = np.where(shared_rois[user] >= min_shared_x)
    return neighbours[0]

def compare_vectors_with_shared_matrix(vector_a,vector_b,rois_a,rois_b,shared_rois,limit,min_shared):
    a_matrix = np.ones((limit, limit)) * 10000
    init_time = time.time()
    for i in range(limit):
        rois_abril = rois_a[i]
        for j in range(limit):
            rois_septiembre = rois_b[j]
            min_shared_x = min(len(rois_abril),len(rois_septiembre),min_shared)
            share_RoIs = shared_rois[i,j]
            if share_RoIs >= min_shared_x:
                a_sequence = vector_a[i]
                b_sequence = vector_b[j]
                dist = abs(np.linalg.norm(np.asarray(a_sequence)-np.asarray(b_sequence)))
                a_matrix[i,j] = dist
    delta_time = time.time() - init_time
    print delta_time
    return a_matrix

#revisa si las features filtro son iguales en ambos vectores
def equalFeatures(a_vector,b_vector,features,filters):
    for f in filters:
        if len(a_vector) != len(b_vector):
            raise lengthsDontMatch()
        try:
            index = features.index(f)
        except KeyError:
            raise FeatureDoesntExist()
        try:
            if a_vector[index] != b_vector[index]:
                return False
        except IndexError:
            print a_vector[0][0]
            print b_vector
            raise IndexError
    return True

#Cual es el formato de los rois??
def compare_vectors_with_neighbours_normalized_fdist(vector_a,vector_b,rois_a,rois_b,shared_rois,limit,min_shared,f_dist,features=None,features_dict=None):
    a_matrix = np.ones((limit, limit)) * -100
    init_time = time.time()
    for i in range(limit):
        #print "Usuario ",i
        rois_abril = rois_a[i][0] #
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
                    if not features:
                        try:
                            dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]))
                        except ValueError:
                            print np.asarray(ab_sequences[0,:])
                            print np.asarray(ab_sequences[counter+1,:])
                            raise ValueError
                    else:
                        dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]),features,features_dict)
                    a_matrix[i,neighbour] = -dist
                    counter += 1
    delta_time = time.time() - init_time
    print delta_time
    return a_matrix

def compare_vectors_with_neighbours_normalized_fdist_filters(vector_a,vector_b,rois_a,rois_b,shared_rois,limit,min_shared,f_dist,features=None,filters=None,features_dict=None):
    a_matrix = np.ones((limit, limit)) * -100
    init_time = time.time()
    for i in range(limit):
        #print "Usuario ",i
        rois_abril = rois_a[i][0] #
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
                    if not filters:
                        if not features_dict:
                            try:
                                dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]))
                            except ValueError:
                                print np.asarray(ab_sequences[0,:])
                                print np.asarray(ab_sequences[counter+1,:])
                                raise ValueError
                        else:
                            dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]),features,features_dict)
                    else:
                        if equalFeatures(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]),features,filters):
                            if not features_dict:
                                try:
                                    dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]))
                                except ValueError:
                                    print np.asarray(ab_sequences[0,:])
                                    print np.asarray(ab_sequences[counter+1,:])
                                    raise ValueError
                            else:
                                dist = f_dist(np.asarray(ab_sequences[0,:]),np.asarray(ab_sequences[counter+1,:]),features,features_dict)
                        else:
                            dist = 100
                    a_matrix[i,neighbour] = -dist
                    counter += 1
    delta_time = time.time() - init_time
    print delta_time
    return a_matrix


def compare_vectors_with_neighbours_normalized(vector_a,vector_b,rois_a,rois_b,shared_rois,limit,min_shared):
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
                    dist = abs(np.linalg.norm(np.asarray(ab_sequences[0,:])-np.asarray(ab_sequences[counter+1,:])))
                    a_matrix[i,neighbour] = dist
                    counter += 1
    delta_time = time.time() - init_time
    #print delta_time
    return a_matrix


#Función que identifica cuantos rois comparten cada par de rois de dos cortes temporales (ct)
#get_shared_rois: list(list(dict)) list(list(dict)) int -> [[int]] list(int)
def get_shared_rois(rois_ct1,rois_ct2,limit):
    init_time = time.time()
    shared = np.ones((limit, limit)) * -1
    min_distance = []
    min_distance_not_shared = -1
    for i in range(limit):
        rois_i = rois_ct1[i]
        for j in range(limit):
            rois_j = rois_ct2[j]
            share_RoIs,min_distance_not_shared = share_rois(rois_i[0],rois_j[0])
            if i==j:
                min_distance.append(min_distance_not_shared)
                min_distance_not_shared = -1
            shared[i,j] = share_RoIs
    delta_time = time.time() - init_time
    print delta_time
    return [shared,min_distance]

#Función que identifica cuantos rois comparten dos grupos de rois y cual es la minima distancia que se descarta como
#rois compartidos
#share_rois: list(dict) list(dict) -> [int,int]
def share_rois(rois_a,rois_b):
    shared = 0
    rois = [rois_a,rois_b]
    index = np.argmin([len(rois_a),len(rois_b)])
    other_index = abs(index-1) 
    min_distance = -1
    for i in range(len(rois[index])):
        an_a_roi = rois[index][i]
        lat_a_roi = an_a_roi['lat']
        long_a_roi = an_a_roi['long']
        for j in range(len(rois[other_index])):
            an_b_roi = rois[other_index][j]
            lat_b_roi = an_b_roi['lat']
            long_b_roi = an_b_roi['long']
            a_distance = vincenty((lat_a_roi,long_a_roi),(lat_b_roi,long_b_roi)).meters
            if a_distance < 500:
                shared +=1
            elif min_distance == -1 or min_distance > a_distance:
                min_distance = a_distance
    return [shared,min_distance]


class lengthsDontMatch(Exception):
    def __init__():
        pass
class FeatureDoesntExist(Exception):
    def __init__():
        pass

def special_diff(a_vector,b_vector,features,features_dict):
    if len(a_vector) != len(b_vector):
        raise lengthsDontMatch()
    vector_diff = []
    for i in range(len(a_vector)):
        try:
            index = features_dict[features[i]]
        except KeyError:
            raise FeatureDoesntExist()
        #temporal variables
        a_value = a_vector[i]
        b_value = b_vector[i]
        if index in [0,1,2,3]:
            try:
                #casos nan
                if a_value != a_value or b_value != b_value:
                    continue
                vector_diff.append(abs(a_value-b_value))
            except ValueError:
                print a_vector
                print b_vector
                raise ValueError  
        #spatial variables
        elif index in [4,5,6,7,8,9,10,11,12,13]:
            #casos nan, no hubo viajes
            if a_value != a_value:
                a_value = 0
            if b_value != b_value:
                b_value = 0
            vector_diff.append(abs(a_value-b_value))
        #card types
        elif index == 14:
            if a_value == b_value:
                vector_diff.append(0)
            else:
                vector_diff.append(1)
        #activity
        elif index in [15,16,17,18,19,20,24,25,26,27,28]:
            if a_value != a_value:
                a_value = 0
            if b_value != b_value:
                b_value = 0
            vector_diff.append(abs(a_value-b_value))
        elif index in [21,22,23]:
            #casos nan
            if a_value != a_value or b_value != b_value:
                continue
            vector_diff.append(abs(a_value-b_value))
        else:
            raise FeatureDoesntExist()
    return vector_diff

def special_euclidean_distance(a_vector,b_vector,features,features_dict):
    vector_diff = special_diff(a_vector,b_vector,features,features_dict)
    return np.linalg.norm(vector_diff)

def special_manhattan_distance(a_vector,b_vector,features,features_dict):
    vector_diff = special_diff(a_vector,b_vector,features,features_dict)
    return sum(vector_diff)