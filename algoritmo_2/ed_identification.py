#Edit distance identification

def cost(a_tuple):
	return a_tuple

def delete(sequence,i,c):
	n = len(sequence)
	sum_lat = 0
	sum_long = 0
	sum_temp = 0
	for seq in sequence:
		sum_lat += seq[0]
		sum_long += seq[1]
		sum_temp += seq[2]
	lat_distance = (sum_lat/n-(sum_lat-sequence[i][0])/(n-1))**2
	long_distance = (sum_long/n-(sum_long-sequence[i][1])/(n-1))**2
	temporal_distance = (sum_temp/n-(sum_temp-sequence[i][2])/(n-1))**2
	spatial_distance = lat_distance + long_distance
	return ((1-c)*spatial_distance+c*temporal_distance)**0.5

def insert(sequence,i,c):
	return 0 
	
#sequence_a: S(s1,....sn)
#sequence_b: T(t1,....tn)
def get_edit_distance(sequence_a,sequence_b,i,j):
	#3 casos

	#s_i deleted and s1,.....,s_i-1 is transformed to t1,....,tj
	d1 = get_edit_distance(sequence_a,sequence_b,i-1,j) + cost(delete(sequence_a,i))
	#s1,....si is transformed into t1,....,t_j-1 and we insert t_j at the end
	d2 = get_edit_distance(sequence_a,sequence_b,i,j-1) + cost(insert(sequence_b,j))
	#s_i is changed into tj and the rest s1,....,s_i-1 is transformed to t1,....,t_j-1
	d3 = get_edit_distance(sequence_a,sequence_b,i-1,j-1) + cost(replace(sequence_a,sequence_b,i,j))

	return min(d1,d2,d3)

def get_sequence(tiempos,par_subidas,par_bajadas):
	#parecido al de tpm pero 
	return []