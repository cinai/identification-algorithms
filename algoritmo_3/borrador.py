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
# Auxiliar Functions

def split_sequence_by_weekdays(df_sequence):
	weekday = df_sequence.query('weekday != 5 and weekday != 6')
	weekend = df_sequence.query('weekday == 5 or weekday == 6')
	return [weekday.reset_index(drop=True), weekend.reset_index(drop=True)]	

# Funcion que busca una locacion en el arreglo mls y retorna el indice
# buscar_locacion: [string] string -> int
def buscar_locacion(mls,location):
	try:
		index_location = mls.index(location)
	except ValueError:
		index_location = -1
	return index_location

### The big function
#TODO: check if tiemposubida hay nan! para despues checkear timediff
def get_features(df_sequence):
	# variables auxiliares
	par_subida = ""; par_bajada = ""
	last_stop = "";	last_lat = "";last_long = ""; last_trip_stop = "";
	last_trip = -1; last_week_day = -1;
	card_type = -1
	n_days = -1 # -1 para acceder al arreglo cuando es 1(0)
	traveled_days_bs = 0
	traveled_days_in_between = 0
	shortest_activities = []; longest_activities = []
	locations = [];	location_set = []; origin_location_set = []
	last_origins = []; first_origins = []; last_origin = None
	start_times = []; end_times = []; an_end_time = None
	pi_locations = []
	n_trips_per_day = []
	n_trips = 0
	rm = np.array([0,0])
	distance = 0; max_distance = 0; min_distance = 10.0**8; a_trip_distance = 0
	step_counter = 0
	exclusive_bus_days = 0.0
	bus_exclusive = False
	exclusive_metro_days = 0.0
	metro_exclusive = False
	bus_counter = 0.0

	# iteracion sobre las etapas
	# TODO: check if it can be somehow faster than this
	for index,stage in df_sequence.iterrows():
		# Card Type Feature
		if card_type == -1 and pd.notnull(stage.adulto):
			card_type = stage.adulto
		weekday = stage.tiempo_subida.weekday()
		if  weekday != last_week_day :
			if last_week_day != -1:
				# last origin feature
				if last_origin:
					last_origins.append(last_origin)
				last_origin = None
				if an_end_time:
					end_times.append(int(auxiliar_functions.hour_to_seconds(an_end_time)))
					an_end_time = None
			#que oasa si no hay tiempo???
			start_times.append(int(auxiliar_functions.hour_to_seconds(stage.tiempo_subida)))
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		#Si es un nuevo viaje debo checkear si hay nuevos indicadores
		#Max Distance and Min Distance Feature 
		if stage.netapa == 1:
			if a_trip_distance > max_distance:
				max_distance = a_trip_distance
			if a_trip_distance < min_distance and a_trip_distance != 0:
				min_distance = a_trip_distance
			a_trip_distance = 0
			last_trip_stop = ""
			last_origin = par_subida
			an_end_time = stage.tiempo_subida	
		#Si existe par subida puedo fijarlo como paradero de origen
		#A veces existe paradero pero no la latitud
		if par_subida == par_subida:
			if stage.weekday != last_week_day:
				# first origin feature
				first_origins.append(par_subida)
			location_index = buscar_locacion(location_set,stage.par_subida)
			if location_index > -1:
				pi_locations[location_index] += 1
			else:
				if stage.netapa == 1:
					origin_location_set.append(par_subida)
				location_set.append(stage.par_subida)
				pi_locations.append(1)
			# radius of gyration
			if stage.lat_subida == stage.lat_subida and stage.long_subida == stage.long_subida:
				locations.append(np.array([stage.lat_subida,stage.long_subida]))
				rm = rm + np.array([stage.lat_subida,stage.long_subida])
				#others
				origin_stop = par_subida
				origin_lat = stage.lat_subida
				origin_long = stage.long_subida 
				#distancia total y distancia parcial        
				if last_stop != "":
					distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
				if last_trip_stop != "":
					a_trip_distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
				if par_bajada != par_bajada or stage.lat_bajada != stage.lat_bajada or stage.long_bajada != stage.long_bajada:
					last_stop = origin_stop
					last_lat = origin_lat
					last_long = origin_long
					last_trip_stop = origin_stop
				else :
					destinatination_stop = par_bajada
					destination_lat = stage.lat_bajada
					destination_long = stage.long_bajada
					distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
					a_trip_distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
					last_stop = destinatination_stop
					last_trip_stop = destinatination_stop
					last_lat = destination_lat
					last_long = destination_long
		#mean shortest activity 
		if  weekday != last_week_day :
			if last_week_day != -1:
				diff = abs(weekday - last_week_day)%6
				if diff > 1:
					traveled_days_bs = traveled_days_in_between
					traveled_days_in_between = 0
				traveled_days_in_between += 1
				n_trips_per_day.append(n_trips)
				while(diff > 1):
					n_trips_per_day.append(0)
					diff -= 1
			if bus_exclusive:
				exclusive_bus_days += 1
			if metro_exclusive:
				exclusive_metro_days += 1
			shortest_activities.append(np.nan)	
			longest_activities.append(np.nan)
			bus_exclusive = True
			metro_exclusive = True
			last_trip = -1
			n_days += 1
			n_trips = 0
			last_week_day = weekday
		if stage.tipo_transporte == "METRO":
			bus_exclusive = False
		if stage.tipo_transporte != "METRO":
			metro_exclusive = False
			bus_counter += 1
		if stage.netapa == 1 :
			n_trips += 1
			last_trip = stage.nviaje
			if stage.nviaje != 1:
				#msal: mean shortest activity length
				#mlal: mean longest activity length
				time_diff = auxiliar_functions.td_to_minutes(stage.diferencia_tiempo)
				#la diferencia de tiempo entre el ultimo viaje y 
				#el nuevo viaje TODO:Fix#sobre estimado ya que considera el tiempo del ultimo viaje
				if shortest_activities[n_days] != shortest_activities[n_days]:
					shortest_activities[n_days] = time_diff
					longest_activities[n_days] = time_diff
				elif shortest_activities[n_days] > time_diff :
					shortest_activities[n_days] = time_diff
				if longest_activities[n_days] < time_diff:
					longest_activities[n_days] = time_diff
		step_counter += 1

	traveled_days = n_days + 1 #n_days parte de 0
	# capturar datos sobre el ultimo viaje
	if a_trip_distance > max_distance:
		max_distance = a_trip_distance
	if a_trip_distance < min_distance and a_trip_distance != 0:
		min_distance = a_trip_distance
	if last_origin:
		last_origins.append(last_origin)
	if bus_exclusive:
		exclusive_bus_days += 1
	if metro_exclusive:		
		exclusive_metro_days += 1
	p100_exclusive_bus_days = exclusive_bus_days/traveled_days*100
	p100_exclusive_metro_days = exclusive_metro_days/traveled_days*100
	P100_bus_trips = bus_counter/step_counter*100
	# percentage different last origins
	last_origin_set = set(last_origins)
	if len(last_origins) > 0:
		p100_diff_last_origin = len(last_origin_set)*1.0/len(last_origins)*100
	else: 
		p100_diff_last_origin = 0.0
	first_origin_set = set(first_origins)
	if len(first_origins) > 0:
		p100_diff_first_origin = len(first_origin_set)*1.0/len(first_origins)*100
	else:
		p100_diff_first_origin = 0.0
	# start times
	start_time = int(np.mean(start_times))
	if an_end_time:
		end_times.append(int(auxiliar_functions.hour_to_seconds(an_end_time)))
	end_time = int(np.mean(end_times))
	traveled_days_bs = traveled_days_in_between if traveled_days_bs == 0 else traveled_days_bs
	#obtener probabilidad de estar en cada locacion 
	pi_suma = sum(pi_locations)
	pi_locations[:] = [x*1.0/pi_suma for x in pi_locations]
	unc_entropy = 0.0
	for pi in pi_locations:
		unc_entropy = unc_entropy + pi*np.log2(pi)
	unc_entropy = -unc_entropy
	if len(origin_location_set) > 0:
		random_entropy = np.log2(len(origin_location_set))
	else:
		random_entropy = 0.0
	#calcular rg
	rm = rm/len(locations)
	rg_suma = 0.0
	#orden n :c
	for r in locations:
		rg_distance = vincenty((r[0],r[1]),(rm[0],rm[1])).meters
		rg_suma = rg_suma + rg_distance**2
	if len(locations) > 0 :
		rg = (rg_suma/len(locations))**0.5
	else:
		rg = 0.0
	msal = np.nanmean(shortest_activities)
	mlal = np.nanmean(longest_activities)
	kmDistance = distance/1000
	kmMaxDist = max_distance/1000
	kmMinDist = min_distance/1000
	card_type = int(card_type)
	n_trips_per_day.append(n_trips) # se entrega???
	frequence_regularity = stats.mode(n_trips_per_day).count[0]
	return [msal,mlal,kmDistance,kmMaxDist,kmMinDist,rg,unc_entropy, \
	random_entropy,p100_diff_last_origin,p100_diff_first_origin,card_type,\
	start_time,end_time,traveled_days,traveled_days_bs,frequence_regularity,\
	p100_exclusive_bus_days,p100_exclusive_metro_days,P100_bus_trips]
