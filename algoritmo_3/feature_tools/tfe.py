# -*- coding: utf-8 -*-
# module tfe: Travel Feature Extracture library

# CUIDADO con los nombres de las columnas, deben ser:
import numpy as np
import pandas as pd
from geopy.distance import vincenty
import auxiliar_functions
from scipy import stats
import scipy.integrate as integrate
from scipy.cluster.hierarchy import linkage, fcluster
from borrador import get_features
def general_feature_extraction(df_sequence):
	weekday,weekend = split_sequence_by_weekdays(df_sequence)
	if weekday.empty:
		time_first_journey_weekday = np.nan
		time_last_journey_weekday= np.nan
		percentage_different_first_origin_weekday = np.nan
		percentage_different_last_origin_weekday = np.nan
		shortest_activity_length_weekday = np.nan
		longest_activity_length_weekday = np.nan
		mean_trips_weekdays = 0
	else:
		time_first_journey_weekday = get_mean_start_time_first_trip(weekday)
		time_last_journey_weekday = get_mean_start_time_last_trip(weekday) 
		percentage_different_first_origin_weekday = get_percentage_different_first_origin(weekday)
		percentage_different_last_origin_weekday = get_percentage_different_last_origin(weekday)
		shortest_activity_length_weekday = get_mean_shortest_activity_length(weekday)
		longest_activity_length_weekday = get_mean_longest_activity_length(weekday)
		mean_trips_weekdays = get_mean_n_trips(weekday)
	if weekend.empty:
		time_first_journey_weekend = np.nan
		time_last_journey_weekend = np.nan
		percentage_different_first_origin_weekend = np.nan
		percentage_different_last_origin_weekend = np.nan
		shortest_activity_length_weekend = np.nan
		longest_activity_length_weekdend = np.nan
		mean_trips_weekend = 0
	else:
		time_first_journey_weekend = get_mean_start_time_first_trip(weekend) 
		time_last_journey_weekend = get_mean_start_time_last_trip(weekend) 
		percentage_different_first_origin_weekend = get_percentage_different_first_origin(weekend)
		percentage_different_last_origin_weekend= get_percentage_different_last_origin(weekend)
		shortest_activity_length_weekend = get_mean_shortest_activity_length(weekend)
		longest_activity_length_weekdend = get_mean_longest_activity_length(weekend)
		mean_trips_weekend = get_mean_n_trips(weekend)
	mode_n_trips = get_mode_trips_per_day(df_sequence)
	most_frequent_number_of_stages = get_most_frequent_number_of_stages(df_sequence)

	[msal,mlal,kmDistance,kmMaxDist,kmMinDist,rg,unc_entropy, \
	random_entropy,p100_diff_last_origin,p100_diff_first_origin,card_type,\
	start_time,end_time,traveled_days,traveled_days_bs,frequence_regularity,\
	p100_exclusive_bus_days,p100_exclusive_metro_days,P100_bus_trips] = get_features(df_sequence)

	return [time_first_journey_weekday,time_last_journey_weekday,\
	time_first_journey_weekend,time_last_journey_weekend,kmDistance,\
	kmMaxDist,kmMinDist,rg,unc_entropy, \
	random_entropy,percentage_different_first_origin_weekday \
	,percentage_different_last_origin_weekday,percentage_different_first_origin_weekend, \
	percentage_different_last_origin_weekend,card_type,\
	shortest_activity_length_weekday,longest_activity_length_weekday, \
	shortest_activity_length_weekend,longest_activity_length_weekdend, \
	traveled_days,traveled_days_bs,\
	p100_exclusive_bus_days,p100_exclusive_metro_days,P100_bus_trips, \
	mode_n_trips,frequence_regularity,mean_trips_weekdays,mean_trips_weekend,most_frequent_number_of_stages]

# Auxiliar Functions

def split_sequence_by_weekdays(df_sequence):
	weekday = df_sequence.query('weekday != 5 and weekday != 6')
	weekend = df_sequence.query('weekday == 5 or weekday == 6')
	return [weekday.reset_index(drop=True), weekend.reset_index(drop=True)]	

### Activity Features

## Activity length 

# 30
# get_mean_shortests_activity_length: pandas.DataFrame -> Timedelta
# entrega el promedio semanal de la actividad mas corta de cada dia
# el tiempo de una actividad corresponde a la diferencia de tiempo entre dos viajes
def get_mean_shortest_activity_length(df_sequence):
	last_week_day = -1
	shortest_activities = []
	n_days = -1
	for index, stage in df_sequence.iterrows():
		weekday = stage.tiempo_subida.weekday()
		if  weekday != last_week_day and stage.nviaje != 1:
			last_week_day = weekday
			n_days += 1
			shortest_activities.append(np.nan)
		if stage.netapa == 1 and stage.nviaje != 1:
			time_diff = auxiliar_functions.td_to_minutes(stage.diferencia_tiempo)
			if shortest_activities[n_days] != shortest_activities[n_days] or shortest_activities[n_days] > time_diff :
				shortest_activities[n_days] = time_diff
	return np.nanmean(shortest_activities)

# 30
# get_mean_longest_activity_length: pandas.DataFrame -> Timedelta
# entrega el promedio semanal de la actividad mas larga de cada dia
# el tiempo de una actividad corresponde a la diferencia de tiempo entre dos viajes
def get_mean_longest_activity_length(df_sequence):
	last_trip = -1
	last_week_day = -1
	longest_activities = []
	activities_counter = -1
	for index, stage in df_sequence.iterrows():
		weekday = stage.tiempo_subida.weekday()
		if  weekday != last_week_day :
			last_week_day = weekday
			last_trip = -1
			activities_counter += 1
			longest_activities.append(np.nan)
		if stage.netapa == 1 and stage.nviaje != 1 :
			time_diff = auxiliar_functions.td_to_minutes(stage.diferencia_tiempo)
			if longest_activities[activities_counter] != longest_activities[activities_counter] or longest_activities[activities_counter] < time_diff :
				longest_activities[activities_counter] = time_diff

	return np.nanmean(longest_activities)

def get_chronology(df_sequence,lat,llong):
	Cvl = []
	t0 = -1
	the_bool = True
	for index, stage in df_sequence.iterrows():
		if vincenty((lat,llong),(stage.lat_subida,stage.long_subida)).meters < 500:
			if the_bool:
				the_bool = False
				t0 = pd.Timestamp(stage.tiempo_subida.date())
			Cvl.append((stage.tiempo_subida-t0).total_seconds()/60)
			#Cvl.append(stage.tiempo_subida)
	return Cvl

def  get_Ins(chronology,w):
	Ins = []
	us = []
	# split chronology into Uses
	counter = 1
	for t in chronology:
		tx = t-(w*(counter-1))
		if tx > w:
			# foreach us in Uses make a I
			Ins.append(In(us,w))
			us = []
			tx = tx - w
			counter += 1 
		us.append(tx)
	Ins.append(In(us,w))
	return Ins

def min_max(Us,u):
	counter = 0
	for i in Us:
		if i >= u:
			return i - Us[counter-1]
		counter += 1

def In(Us,w):
	return lambda u: Us[0] if u>0 and u <= Us[0] else w-Us[len(Us)-1] if u>Us[len(Us)-1]and u<= w else min_max(Us,u)

def mu(u,I_n):
	a_sum = 0
	for i in I_n:
		a_sum = i(u) + a_sum
	return a_sum/len(I_n)

def ro(u,I_n):
	a_sum = 0
	if len(I_n) == 1:
		return 0.000001
	mu_u = mu(u,I_n)
	for i in I_n:
		a_sum = (i(u) - mu_u) ** 2 + a_sum
	return (a_sum/(len(I_n)-1))**0.5

def c_var(u,I_n):
	return mu(u,I_n)/ro(u,I_n)

## Regularity
# 36
# la regularidad de visitar una locacion
def get_regularity(chronology,window):
	# get inter-visit interval
	#In = lambda c,u,w: c[0] if u>0 and u <= c[0] else w-u[len(c)-1] if u>u[len(c)-1]and u<= w  else min(i for i in c if i > u)
	I_n = get_Ins(chronology,window)
	regularity = integrate.quad(lambda u: c_var(u,I_n), 0, window)
	return regularity[0]/window

### Distance Features

## Travel Distance 
# 33
# get_traveled_distance: pandas.DataFrame -> float
# entrega la distancia total viajada 
def get_traveled_distance(df_sequence):
	last_stop = ""
	last_lat = ""
	last_long = ""
	distance = 0
	for index, stage in df_sequence.iterrows():
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		if par_subida != par_subida:
			continue
		origin_stop = par_subida
		origin_lat = stage.lat_subida
		origin_long = stage.long_subida         
		if last_stop != "":
			distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
		if par_bajada != par_bajada:
			last_stop = origin_stop
			last_lat = origin_lat
			last_long = origin_long
		else :
			destinatination_stop = par_bajada
			destination_lat = stage.lat_bajada
			destination_long = stage.long_bajada
			distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
			last_stop = destinatination_stop
			last_lat = destination_lat
			last_long = destination_long

	return distance/1000
# 30
def get_maximum_travel_distance(df_sequence):
	max_distance = 0
	distance = 0
	for index, stage in df_sequence.iterrows():
		if stage.netapa == 1:
			if distance > max_distance:
				max_distance = distance
			distance = 0
			last_stop = ""
			last_lat = ""
			last_long = ""
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		if par_subida != par_subida:
			continue
		origin_stop = par_subida
		origin_lat = stage.lat_subida
		origin_long = stage.long_subida         
		if last_stop != "":
			distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
		if par_bajada != par_bajada:
			last_stop = origin_stop
			last_lat = origin_lat
			last_long = origin_long
		else :
			destinatination_stop = par_bajada
			destination_lat = stage.lat_bajada
			destination_long = stage.long_bajada
			distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
			last_stop = destinatination_stop
			last_lat = destination_lat
			last_long = destination_long

	if distance > max_distance:
		max_distance = distance
	return max_distance/1000
# 30
# sin contar los dias que no viaja?
def get_minimum_travel_distance(df_sequence):
	min_distance = 10.0**8
	distance = 0
	for index, stage in df_sequence.iterrows():
		if stage.netapa == 1:
			if distance < min_distance and distance != 0:
				min_distance = distance
			distance = 0
			last_stop = ""
			last_lat = ""
			last_long = ""
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		if par_subida != par_subida:
			continue
		origin_stop = par_subida
		origin_lat = stage.lat_subida
		origin_long = stage.long_subida         
		if last_stop != "":
			distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
		if par_bajada != par_bajada:
			last_stop = origin_stop
			last_lat = origin_lat
			last_long = origin_long
		else :
			destinatination_stop = par_bajada
			destination_lat = stage.lat_bajada
			destination_long = stage.long_bajada
			distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
			last_stop = destinatination_stop
			last_lat = destination_lat
			last_long = destination_long

	if distance < min_distance and distance != 0:
		min_distance = distance
	return min_distance/1000
# 33. 13 17
# solo considera las subidas
def get_radius_of_gyration(df_sequence):
	locations = []
	rm = np.array([0,0])
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			locations.append(np.array([stage.lat_subida,stage.long_subida]))
			rm= rm + np.array([stage.lat_subida,stage.long_subida])
	rm = rm/len(locations)
	suma = 0.0
	for r in locations:
		distance = vincenty((r[0],r[1]),(rm[0],rm[1])).meters
		suma = suma + distance**2
	return (suma/len(locations))**0.5

## OD Frecuency
# Considera la secuencia temporal pero no los tiempos
# Está malo, falta informacion de como obtienen los substring
def get_entropy(df_sequence):
	day_sequence = ""
	sequences = []
	p_sequences = []
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday and last_weekday > -1:
			indice = buscar_locacion(sequences,day_sequence)
			if indice > -1:
				p_sequences[indice] += 1
			else:
				sequences.append(day_sequence)
				p_sequences.append(1)
			day_sequence = ""
		if stage.par_subida == stage.par_subida:
			day_sequence = day_sequence + stage.par_subida
			last_weekday = stage.weekday
	indice = buscar_locacion(sequences,day_sequence)
	if indice > -1:
		p_sequences[indice] += 1
	else:
		sequences.append(day_sequence)
		p_sequences.append(1)
	la_suma = sum(p_sequences)
	p_sequences[:] = [x*1.0/la_suma for x in p_sequences]
	entropy = 0.0
	for p in p_sequences:
		entropy = entropy + p * np.log2(p)
	return -entropy
# Funcion que busca una locacion en el arreglo mls y retorna el indice
# buscar_locacion: [string] string -> int
def buscar_locacion(mls,location):
	try:
		index_location = mls.index(location)
	except ValueError:
		index_location = -1
	return index_location
#36
def get_unc_entropy(df_sequence):
	pis = get_pi_locations(df_sequence)
	la_suma = 0.0
	for pi in pis:
		la_suma = la_suma + pi*np.log2(pi)
	return -la_suma

#no considera transbordos, ya que exige que sea la primera etapa del viaje
def get_latlong_points(df_sequence):
	a = []
	locations = []
	n_locations = []
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida and stage.netapa == 1:
			if stage.lat_subida == stage.lat_subida and stage.long_subida == stage.long_subida:
				indice = buscar_locacion(locations,stage.par_subida)
				if indice > -1:
					n_locations[indice] += 1
				else:
					a.append(np.array([stage.lat_subida,stage.long_subida]))
					locations.append(stage.par_subida)
					n_locations.append(1)
	la_suma = sum(n_locations)
	n_locations[:] = [x*1.0/la_suma for x in n_locations]
	return [np.asarray(a),locations,n_locations]

def get_pi_locations(df_sequence):
	locations = []
	n_locations = []
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			indice = buscar_locacion(locations,stage.par_subida)
			if indice > -1:
				n_locations[indice] += 1
			else:
				locations.append(stage.par_subida)
				n_locations.append(1)
	la_suma = sum(n_locations)
	n_locations[:] = [x*1.0/la_suma for x in n_locations]
	return n_locations
# 36
def get_random_entropy(df_sequence):
	nl = get_n_different_locations(df_sequence)
	return np.log2(nl)
#36
def get_n_unic_locations():
	return 0
#33 13
# obtiene el numero de locaciones diferentes
# solo considera las subidas de la primera etapa
def get_n_different_locations(df_sequence):
	locations = []
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida and stage.netapa == 1:
			locations.append(stage.par_subida)
	the_set = set(locations)
	return len(the_set)
# 30 
def get_percentage_different_last_origin(df_sequence):
	last_origins = []
	last_weekday = -1
	last_origin = None
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			if last_weekday > -1:
				if last_origin:
					last_origins.append(last_origin)
				last_origin = None
			last_weekday = stage.weekday
		if stage.netapa == 1:
			last_origin = stage.par_subida
	if last_origin :
		last_origins.append(last_origin)
	the_set = set(last_origins)
	if len(last_origins) == 0:
		return np.nan
	return len(the_set)*1.0/len(last_origins)*100

# 30 
# a veces no hay información sobre el paradero, en estos casos se retorna nan
def get_percentage_different_first_origin(df_sequence):
	first_origins = []
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			if stage.par_subida == stage.par_subida:
				first_origins.append(stage.par_subida)
			last_weekday = stage.weekday
	the_set = set(first_origins)
	if len(first_origins) == 0:
		return np.nan
	return len(the_set)*1.0/len(first_origins)*100

def get_upToX_pi_locations(pi_sums,x):
	if x == 1:
		return [range(len(pi_sums)),100]
	the_indexs = []
	the_sum = 0
	while True:
		if the_sum >= x:
			break
		index = pi_sums.argmax()
		the_indexs.append(index)
		the_sum = the_sum + pi_sums[index]
		pi_sums[index] = 0
	return [the_indexs,the_sum]

	
# ?
def get_ROIs(df_sequence,x,limit_meters):
	X,locations,pi_locations = get_latlong_points(df_sequence)
	if len(locations) == 1:
		return [[{"lat":X[0,0],"long":X[0,1]}],1.0]
	elif len(locations) < 1:
		return None
	Z = linkage(X,'weighted',lambda x,y: vincenty(x,y).meters)
	clusters = fcluster(Z,limit_meters,criterion='distance')
	centroids = []
	nums_by_clusters =[]
	pi_sums = []
	the_clusters = []
	for i in range(len(clusters)):
		indice = buscar_locacion(the_clusters,clusters[i])
		if indice < 0:
			the_clusters.append(clusters[i])
			indice = len(the_clusters)-1
			pi_sums.append(0)
			nums_by_clusters.append(0)
			centroids.append({"lat":0,"long":0})
		pi_sums[indice] += pi_locations[i]
		centroids[indice]["lat"] += X[i,0]
		centroids[indice]["long"] += X[i,1]
		nums_by_clusters[indice] += 1

	the_indexs, the_sum = get_upToX_pi_locations(np.asarray(pi_sums),x)
	the_centroids = []
	for i in the_indexs:
		the_centroids.append({"lat":centroids[i]["lat"]/nums_by_clusters[i],"long":centroids[i]["long"]/nums_by_clusters[i]})
	return [the_centroids,the_sum]

def get_clusters(df_sequence):
	X,locations,pi_locations = get_latlong_points(df_sequence)
	Z = linkage(X, 'ward')
	clusters = fcluster(Z,0.02,criterion='distance')
	return clusters

## Regularity
# 33 17 .. en 33 hablan de las PRD PRI, no info
def get_return_degree(df_sequence):
	return 0
# 27 no definen la feature
def get_n_similar_sequences(df_sequence):
	return 0

# 36: hourly not enough data 
# measuring the fraction of instances when the user is found in his or
# her most visited location during the corresponding hour long period.
def get_regularity_dt(df_sequence):

	return 0

### Temporal Features

## Start Time
# 27 no definen la feature
def get_n_similar_start_times():
	return 0
# 30
# funciona muy mal cuando es irregular
def get_mean_start_time_first_trip(df_sequence):
	start_times = []
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			start_times.append(int(auxiliar_functions.hour_to_seconds(stage.tiempo_subida)))
		last_weekday = stage.weekday
	return int(np.nanmean(start_times))
# 30
# funciona muy mal cuando es irregular
#caso raro: cuando hay transacciones pero continuaciones del día anterior, se retorna nan
def get_mean_start_time_last_trip(df_sequence):
	try:
		end_times = []
		last_weekday = -1
		an_end_time = 0
		for index, stage in df_sequence.iterrows():
			if stage.weekday != last_weekday and last_weekday > -1:
				if an_end_time:
					end_times.append(int(auxiliar_functions.hour_to_seconds(an_end_time)))
					an_end_time = None
			if stage.netapa == 1:
				an_end_time = stage.tiempo_subida
			last_weekday = stage.weekday
		end_times.append(int(auxiliar_functions.hour_to_seconds(an_end_time)))
		return int(np.nanmean(end_times))
	except:
 		return np.nan
## Travel Frequency 

# 
def get_n_days_traveled_before_stop(df_sequence):
	traveled_days = 0
	traveled_days_bs = 0
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			if last_weekday != -1:
				diff = (stage.weekday - last_weekday)%6
				if diff > 1:
					traveled_days_bs = traveled_days
					traveled_days = 0
				traveled_days += 1
			last_weekday = stage.weekday

	return traveled_days if traveled_days_bs == 0 else traveled_days_bs
# 30 27
def get_n_days_traveled(df_sequence):
	traveled_days = 0
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			traveled_days += 1
			last_weekday = stage.weekday		
	return 	traveled_days

#30
# hay que rellenar con 0's a la derecha si es que no calzan los dias
def get_n_trips_per_day(df_sequence):
	last_weekday = -1
	last_nviaje = -1
	n_trips_per_day = []
	n_trips = 0
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday and last_weekday > -1:
			days_diff = abs(stage.weekday - last_weekday)%6
			n_trips_per_day.append(n_trips)
			while(days_diff > 1):
				n_trips_per_day.append(0)
				days_diff -= 1
			n_trips = 0
		last_weekday = stage.weekday		
		if stage.nviaje != last_nviaje:
			n_trips += 1
			last_nviaje = stage.nviaje
	n_trips_per_day.append(n_trips)
	
	return n_trips_per_day
# 41
# Cuenta el numero de veces que la moda de la cantidad de viajes ocurre
def get_frequence_regularity(df_sequence):
	n_trips_per_day = get_n_trips_per_day(df_sequence)
	return stats.mode(n_trips_per_day).count[0]
### Sociodemographic Features 

## TODO: check card_type code
# get_card_type: pandas.DataFrame -> int
# Returns the card type of a sequence
# -1 - no information
# 0 - adult
# 1 - other 
def get_card_type(df_sequence):
	card_type = -1
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			card_type = stage.adulto
			break
	return int(card_type)


###  Variability mode of transport 
# 30
# Considera etapas
def get_percentage_bus_exclusive_days(df_sequence):
	traveled_days = -1.0
	exclusive_bus_days = 0.0
	last_weekday = -1
	bus_exclusive = False
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			traveled_days += 1	
			last_weekday = stage.weekday
			if bus_exclusive:
				exclusive_bus_days += 1
			bus_exclusive = True
		elif bus_exclusive == False:
			continue
		if stage.tipo_transporte == "METRO":
			bus_exclusive = False
	# debo sumar uno por la ultima corrida de viajes
	traveled_days += 1	
	if bus_exclusive:
		exclusive_bus_days += 1
	return 	exclusive_bus_days/traveled_days*100
# 30
# Considera etapas
def get_percentage_rail_exclusive_days(df_sequence):
	traveled_days = -1.0
	exclusive_metro_days = 0.0
	last_weekday = -1
	metro_exclusive = False
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			traveled_days += 1	
			last_weekday = stage.weekday
			if metro_exclusive:
				exclusive_metro_days += 1
			metro_exclusive = True

		if stage.tipo_transporte != "METRO":
			metro_exclusive = False
	# debo sumar uno por la ultima corrida de viajes
	traveled_days += 1
	if metro_exclusive:
		exclusive_metro_days += 1
	return 	exclusive_metro_days/traveled_days*100

# inventado
# Considera etapas
def get_percentage_bus_trips(df_sequence):
	bus_counter = 0.0
	for index, stage in df_sequence.iterrows():
		if stage.tipo_transporte != "METRO":
			bus_counter += 1
	return bus_counter/len(df_sequence)*100

#cambie el nan por el promedio
def get_most_frequent_number_of_stages(df_sequence):
	try:
		return df_sequence.groupby(['nviaje'])['netapa'].max().mode()[0]
	except IndexError:
		return df_sequence[df_sequence['netapa']==1].groupby(['nviaje'])['netapa'].max().mean()

#a veces no hay moda, se podria considerar el promedio, pero se opto por decir que no hay moda
def get_mode_trips_per_day(df_sequence):
	try:
		mode = df_sequence[df_sequence['netapa']==1].groupby(['date'])['nviaje'].count().mode()
		if len(mode) == 0:
			return df_sequence[df_sequence['netapa']==1].groupby(['date'])['nviaje'].count().mean()
		return mode[0]
	except IndexError:
		return np.nan

def get_mean_n_trips(df_sequence):
	try:
		mean = df_sequence[df_sequence['netapa']==1].groupby(['date'])['nviaje'].count().mean()
		if mean != mean:
			return 0
		return mean
	except IndexError:
		return 0