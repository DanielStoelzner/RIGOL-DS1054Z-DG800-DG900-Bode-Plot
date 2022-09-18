import cmath
import pyvisa as visa
import time
import numpy as np
import matplotlib.pyplot as plt
import math
from ds1054z import DS1054Z
import scipy
from scipy.interpolate import make_interp_spline

config = open('config.txt')
time_delay = 1.2 #Adjust the time delay between frequency increments (in seconds)

freq_start = float(config.readline().split(',')[1])		#Read the start frequency
freq_end = float(config.readline().split(',')[1])		#Read the end frequency
if freq_start < 0 or freq_end < 0:
	print('ERROR. Frequency must be positive')
	print('Please press Enter to exit')
	input()
	exit(1)
if freq_start > freq_end:
	print('ERROR. Start Frequency must be less than End Frequency')
	print('Please press Enter to exit')
	input()
	exit(1)

freq_steps = int(config.readline().split(',')[1])			#Read the frequency steps
if freq_steps <= 0:
	print('ERROR. Frequency steps must be greater than zero')
	print('Please press Enter to exit')
	input()
	exit(1)
	
wave_v_max = float(config.readline().split(',')[1])		#Read the max voltage of sine wave
if wave_v_max <= 0:
	print('ERROR. Max Voltage must be greater than zero')
	print('Please press Enter to exit')
	input()
	exit(1)

sweep = config.readline().split(',')[1]
sweep = sweep[:-1]
if sweep != 'log' and sweep != 'lin':
	print("ERROR. Sweep type must be either 'log' or 'lin'")
	print('Please press Enter to exit')
	input()
	exit(1)

scale = config.readline().split(',')[1]
scale = scale[:-1]
if scale != 'db' and scale != 'v':
	print("ERROR. Scale must be either 'db' or 'v'")
	print('Please press Enter to exit')
	input()
	exit(1)

freqs = np.zeros(freq_steps)

if sweep == 'log':
	freqs = np.logspace(np.log10(freq_start), np.log10(freq_end), num=freq_steps)
else:
	freqs = np.linspace(freq_start, freq_end, num=freq_steps)

instrument = config.readline().split(',')[1]
instrument = instrument[:-1]

instrument2 = config.readline().split(',')[1]
instrument2 = instrument2[:-1]

print("-"*32)
print("Configuration:")
print("Start Frequency: " + str(freq_start))
print("End Frequency: " + str(freq_end))
print("Frequency Steps: " + str(freq_steps))
print("Max Voltage: " + str(wave_v_max))
print("Sweep Type: " + str(sweep))
print("Scale: " + scale)
print("Scope ID: " + instrument)
print("AWG ID: " + instrument2)
print("-"*32)
print(" ")

rm = visa.ResourceManager()						#PyVISA Resource Manager

try:
	try:
		scope = DS1054Z(instrument)
	except:
		print("Scope: not found")
		raise Exception() 
		
	print ("Scope: " + scope.idn)

	scope.write("MEASure:CLEar ALL")					#Clear all measurement items
	scope.write("MEASure:ITEM VPP,CHANnel1")			#Create the VMax measurement item for CH1
	scope.write("MEASure:ITEM VPP,CHANnel2")			#Create the VMax measurement item for CH2

	try:
		awg = rm.open_resource(instrument2)
	except:
		print("AWG: not found")
		raise Exception()

	print ("AWG: " + awg.query("*IDN?"))
	
except:
	print('Please press Enter to exit')
	input()
	exit(1)
	
awg.write(':SOURce1:FUNC SINusoid')
awg.write(':SOURce1:FREQ '+str(freq_start))
awg.write(':OUTPut1 ON')
awg.write(':SOUR1:VOLTage:HIGH '+str(wave_v_max/2))
awg.write(':SOUR1:VOLTage:LOW -'+str(wave_v_max/2))
awg.write(":OUTPut1:IMP INF")			#Init the CH1 of generator

time.sleep(1)

ch1_vpp = np.zeros(freq_steps)				#Create an array for CH1 measurements
ch2_vpp = np.zeros(freq_steps)				#Create an array for CH2 measurements
db = np.zeros(freq_steps)					#Create an array for the result in db
freq_values = np.zeros(freq_steps)				#Create an array for values of frequency
phase_values = np.zeros(freq_steps)

freq = freq_start

scope.write("TIMebase:MAIN:SCAle " + str(1/(4*freq)))	#Set horizontal scale of oscilloscope

scope.write("CHANnel1:SCALe 5")
scope.write("CHANnel2:SCALe 5")

time.sleep(.2)
scope.set_channel_scale(1, float(scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel1")) / 4, use_closest_match=True)
time.sleep(.2)
scope.set_channel_scale(2, float(scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel2")) / 4, use_closest_match=True)

scope.write("MEASure:SETup:PSA CHANnel1")	#Setup CH1 as reference to measure phase
scope.write("MEASure:STATistic:ITEM RPHase")	#Setup CH1 as reference to measure phase
scope.write(":MEASure:STATistic:RESet")

i = 0

while i < freq_steps:
	awg.write(':SOUR1:FREQ '+str(freqs[i]))						#Set CH1 (gen) frequency 
	scope.write("TIMebase:MAIN:SCAle "+ str(1/(4*freqs[i])))		#Set the horizontal scale of oscilloscope
	scope.write(":MEASure:STATistic:RESet")
	time.sleep(time_delay)						#Time delay
	ch1_vpp[i] = scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel1")	#Read and save CH1 VMax
	ch2_vpp[i] = scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel2")	#Read and save CH2 Vmax
	phase_values[i] = scope.query("MEASure:STATistic:ITEM? AVERages,RPHase")
	freq_values[i] = freqs[i]						#Save actual frequency
	print (str(i+1) + '/' + str(freq_steps) + ' ' + f'{round(freqs[i],2):,}' + 'Hz')
	scope.set_channel_scale(2, ch2_vpp[i] / 4, use_closest_match=True)
	i = i + 1							#Increment index
	
print("-"*32)

def find_nearest(array, value):
	array = np.asarray(array)
	idx = (np.abs(array - value)).argmin()
	return idx

if scale == 'db':
	db = (ch2_vpp/ch1_vpp)				#Cocient between ch2_vpp and ch1_vpp (for compute db)
	db = 20*np.log10(db)				#Compute db
	
	fig_db = plt.figure(1)
	plt.plot(freq_values,db,alpha=0.75)				#Graph data
	
	X_Y_Spline = make_interp_spline(freq_values, db)
	X_ = np.linspace(freq_values.min(), freq_values.max(), 200)
	Y_ = X_Y_Spline(X_)
	plt.plot(X_, Y_, "--", color="red", label="Smoothed data")
	
	freq_cutoff = X_[find_nearest(Y_, value=-3.0)]
	
	plt.axhline(-3.0, color = 'orchid', linestyle = ':', label = '-3dB')
	plt.axvline(freq_cutoff, color = 'orange', linestyle = ':', label = 'Cutoff Frequency (~ ' + str(round(freq_cutoff, 2)) + "Hz)")
	plt.xlabel('f')
	plt.ylabel('dB')
	plt.title('Magnitude Bode Plot')
	plt.grid()
	if sweep == 'log':
		plt.xscale("log")
	plt.legend()

elif scale == 'v':
	fig_db = plt.figure(1)
	plt.plot(freq_values,ch2_vpp,alpha=0.75)			#Graph data

	X_Y_Spline = make_interp_spline(freq_values, ch2_vpp)
	X_ = np.linspace(freq_values.min(), freq_values.max(), 200)
	Y_ = X_Y_Spline(X_)
	plt.plot(X_, Y_, "--", color="red", label="Smoothed data")
	
	plt.xlabel('f')
	plt.ylabel('Vout')
	plt.title('V Bode Plot')
	plt.grid()
	if sweep == 'log':
		plt.xscale("log")
	plt.legend()
	
fig_phase = plt.figure(2)
plt.plot(freq_values, phase_values,alpha=0.75)				#Graph data

X_Y_Spline = make_interp_spline(freq_values, phase_values)
X_ = np.linspace(freq_values.min(), freq_values.max(), 200)
Y_ = X_Y_Spline(X_)

plt.plot(X_, Y_, "--", color="red", label="Smoothed data")

if scale == 'db':
	plt.axvline(freq_cutoff, color = 'orange', linestyle = ':', label = 'Cutoff Frequency (~ ' + f'{round(freq_cutoff,2):,}' + "Hz)")
plt.xlabel('f')
plt.ylabel('°')
plt.title('Phase Bode Plot')
plt.grid()
if sweep == 'log':
	plt.xscale("log")
plt.legend()

awg.write(':OUTPut1 OFF')

plt.show()

scope.close()					#Stop communication with oscilloscope
awg.close()
