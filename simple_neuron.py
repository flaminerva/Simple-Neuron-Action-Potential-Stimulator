import matplotlib.pyplot as plt
import numpy as np

class SimpleNeuron():


    """This is a simple neuron action potential simulation. """


    def __init__(self): #all of the parameters based on real bio(from papers)
       ### SI UNIT
       #Time: ms
       #Voltage: mV
       #Concentration: mM = mmol/L



        self.state = 'resting'

        self.Na_channel = False
        self.K_channel = False
        self.Na_K_pump = True

        self.Na_in = 15.0
        self.Na_out = 145.0
        self.K_in = 150.0
        self.K_out = 5.0

        #stiumulate the absulote refractory peroid
        #1.0 H_gate open completely
        #0.0 H_gate close completely
        #parameters come from the HH equation
        self.Na_h_gate = 1.0 #Na channel has one h gate
        self.Na_m_gate = 0.05 #Na channel has 3 m gates
        self.Na_stim_m = 0.0
        self.K_n_gate = 0.32

        #permeability
        self.p_Na = 0.04
        self.p_K = 1.0

        #Physical constant
        self.R = 8.314 #J/(mol.K)
        self.T = 310 #K
        self.F = 96485 #C/mol
        self.RT_F = (self.R*self.T /self.F) *1000 #mV
        self.EPS = 1e-6 #avoid log error

        #Conductance mS/cm^2
        self.g_Na_max = 120
        self.g_K_max = 36.0
        self.g_leak = 0.3
        self.E_leak = -70.0
        self.C_m = 1 #μF/cm²
        self.r_c_cm = 1e-3 # ~10 μm
        self.v_o_a = self.r_c_cm / 3.0
        self.fac = 1e-3/(self.F*self.v_o_a)

        #ms
        self.tau_h = 7.0 #ms h_gate inactivation time
        self.tau_m = 1.0 #ms m_gate activation time
        self.tau_stim = 0.5

        self.I_pump_max = 0.5 # μA/cm²=C/s*cm^2
        self.K_Na = 10.0 # mM 半饱和浓度 Michaelis constant
        self.K_K = 1.5

        self.dt = 0.01 #ms
        self.voltage = self.calculate_voltage()



    def calculate_eq(self,ion): #use Nernst equation
        if ion == 'Na':
            E_Na = self.RT_F*np.log(self.Na_out/self.Na_in)
            return E_Na
        elif ion == 'K':
            E_K = self.RT_F*np.log(self.K_out/self.K_in)
            return E_K

    def calculate_voltage(self): #use Goldman equation
        nume = self.p_K*self.K_out + self.p_Na*self.Na_out
        denom = self.p_K*self.K_in + self.p_Na*self.Na_in

        V_m = self.RT_F*np.log(nume / denom)

        return V_m

    def pump_cycle(self): #use Michaelis-Menten
        #Here is the pump, noticed that there are some problems due to the parameters, so when you close it, the change will not be noticed immediately, i'm trying to fix it
        v_Na = self.Na_in / (self.Na_in + self.K_Na) #反应速率
        v_K = self.K_out / (self.K_out + self.K_K)

        I_pump = self.I_pump_max * v_Na * v_K  #based on the Concentration of ions


        if self.Na_K_pump: #positive channel 3Na out 2K in
            #K_rate = 0.02 #mM/ms

            d_Na_dt_p = 3*I_pump * self.fac #mM/ms
            d_K_dt_p = 2*I_pump * self.fac #mM/ms

            self.Na_in = max(self.EPS, self.Na_in-d_Na_dt_p*self.dt)
            self.Na_out = max(self.EPS, self.Na_out+d_Na_dt_p*self.dt)
            self.K_in = max(self.EPS, self.K_in+d_K_dt_p*self.dt)
            self.K_out= max(self.EPS, self.K_out-d_K_dt_p*self.dt)

            #self.Na_in = max(self.EPS, self.Na_in-0.03*self.dt) #here the changing parameters based on real biology
            #self.Na_out = max(self.EPS, self.Na_out+0.03*self.dt)
            #self.K_in = max(self.EPS, self.K_in+0.02*self.dt)
            #self.K_out= max(self.EPS, self.K_out-0.02*self.dt)

        else:
            return

    def p_cal(self,ion): #permeability
        if ion == 'Na': #notice in the real experiment, the p_Na changes more obviously than p_K
            self.p_Na_min = 0.04
            self.p_Na_max = 5.0 #i basically just took it from GHK equation but this is too complicated let's just take this parameters simply
            if self.state == 'depolarizing':
                self.Na_m_gate = 1.0 #notice that it's a simple version
            elif self.state == 'repolarizing':
                self.Na_m_gate = 0.3
            elif self.state == 'recovering':
                self.Na_m_gate = 0.1
            elif self.state == 'resting':
                self.Na_m_gate = 0.05
            else:
                self.Na_m_gate = 0.05

            m_b = self.Na_m_gate
            m_p  = np.clip(m_b + self.Na_stim_m, 0.0, 1.0)     # stim up m
            gates = (m_p**3) * self.Na_h_gate                 # m³h
            self.p_Na = self.p_Na_min + (self.p_Na_max - self.p_Na_min) * gates
            #self.p_Na = self.p_Na_min + (self.p_Na_max-self.p_Na_min)*(self.Na_m_gate**3)*self.Na_h_gate
            #return self.p_Na
        elif ion == 'K':
            if self.state == 'resting':
                 self.K_n_gate = 0.32
            elif self.state == 'depolarizing':
                 self.K_n_gate = 0.45
            elif self.state == 'repolarizing':
                 self.K_n_gate = 0.85
            elif self.state == 'recovering':
                 self.K_n_gate = 0.45
            else:
                 self.K_n_gate = 0.32

            #self.p_K_min = 1.0
            self.p_K_max = 2.0
            self.p_K_leak = 1.0
            self.p_K = self.p_K_max * (self.K_n_gate**4)
            self.p_K += self.p_K_leak



    def ion_current(self,ion):
        if ion == 'Na':
            ##this is simple version since m gate actually changes based on voltage
            #you can use formula to caculate based on slope of the voltage but i will make it simple here
            if self.state == 'depolarizing':
                self.Na_m_gate = 1.0 #notice that it's a simple version
            elif self.state == 'repolarizing':
                self.Na_m_gate = 0.3
            elif self.state == 'recovering':
                self.Na_m_gate = 0.1
            elif self.state == 'resting':
                self.Na_m_gate = 0.05
            else:
                self.Na_m_gate = 0.05

            m_b = self.Na_m_gate
            m_p  = np.clip(m_b + self.Na_stim_m, 0.0, 1.0)     # stim up m
            I_Na = self.g_Na_max*self.Na_h_gate*(m_p**3)*(self.voltage-self.calculate_eq('Na'))
            #conductance formula
            #I_Na  = self.g_Na_max*self.Na_h_gate*(self.Na_m_gate**3)*(self.voltage-self.caculate_eq('Na'))
            return I_Na

        elif ion == 'K':
            if self.state == 'resting':
                 self.K_n_gate = 0.32
            elif self.state == 'depolarizing':
                 self.K_n_gate = 0.45
            elif self.state == 'repolarizing':
                 self.K_n_gate = 0.85
            elif self.state == 'recovering':
                 self.K_n_gate = 0.45
            else:
                 self.K_n_gate = 0.32

            I_K  = self.g_K_max*(self.K_n_gate**4)*(self.voltage-self.calculate_eq('K'))
            return I_K

        elif ion == 'leak':
            I_leak  = self.g_leak*(self.voltage-self.E_leak)
            return I_leak



    def d_concentration_ms(self,ion): #calculate the dNa/dt mol/ms

        if ion == 'Na':

            dNa_dt = -self.ion_current('Na')*self.fac  #mM/ms
            return dNa_dt

        elif ion == 'K':
            dK_dt = self.ion_current('K')*self.fac
            return dK_dt


    def can_stimulate(self):
        return self.Na_h_gate>0.8 and self.state=='resting'
        #when h_gate almost recover(the protein removed) and state in resting

    def apply_stimulation(self,strength): #recieve the stimulation will change the voltage
        #here strength is the current injection μA/cm²
        if self.can_stimulate():
             k = 0.009
             self.Na_stim_m = min(1.0, self.Na_stim_m + k * strength * self.dt)


        #here we use membrane capacity equation #actually the effect is not that good so i gave it up
        #C_m × dV/dt = I_stim + I_ion
        #dv_dt = (strength + self.ion_current('Na') + self.ion_current('K') + self.ion_current('leak')) / self.C_m
        #self.voltage += dv_dt*self.dt

            #if self.voltage >= -40:
                #self.state = 'depolarizing'

    def update(self): #update voltage by time/step(stimulate the raising pharse when sodium channels open)


        self.pump_cycle() #background working
        self.Na_stim_m *= np.exp(-self.dt/self.tau_stim)


        if self.state == 'resting':
            self.p_cal('Na')
            self.p_cal('K')
            if self.voltage >= -55:
                self.state = 'depolarizing'
                self.Na_channel = True

            if self.Na_h_gate<1.0:
                #h gate recovering
                self.Na_h_gate += 0.05*self.dt
                self.Na_h_gate = min(1.0, self.Na_h_gate)



            self.voltage = self.calculate_voltage()


        elif self.state == 'depolarizing':
            self.Na_channel = True
            #h gate is closing
            self.Na_h_gate = max(0.0, self.Na_h_gate - 0.2 * self.dt)

            #self.p_Na = min(20.0, self.p_Na + 20.0*dt) #Na_m_gate open p_Na raise rapidly
            #self.p_Na = 6
            self.p_cal('Na')
            self.p_cal('K')

            self.Na_in = max(self.EPS, self.Na_in+self.d_concentration_ms('Na')*self.dt)
            self.Na_out = max(self.EPS, self.Na_out-self.d_concentration_ms('Na')*self.dt)

            self.voltage = self.calculate_voltage()

            if self.voltage >= 30 or self.Na_h_gate<0.2:
                self.state = 'repolarizing'
                self.Na_channel = False
                self.K_channel  = True
                #self.p_Na = 0.04
                #self.p_K  = 2

        elif self.state == 'repolarizing':
            #self.Na_m_gate = 0.02
            #self.Na_h_gate = min(self.Na_h_gate, 0.2)
            self.p_cal('Na')
            self.p_cal('K')
            self.Na_channel = False
            self.K_channel = True
            #self.p_cal('Na')
            #self.p_Na = 0.04 #m_gate close rapidly, here i just simply change to the closing permeability
            #if you want you can use exponential decay with a greater rate
            #self.p_K = min(20.0, self.p_K + 30.0*dt)

            if self.Na_h_gate < 1.0:
                self.Na_h_gate += 0.02 * self.dt

            self.K_out = max(self.EPS, self.K_out+self.d_concentration_ms('K')*self.dt)
            self.K_in = max(self.EPS, self.K_in-self.d_concentration_ms('K')*self.dt)

            self.voltage = self.calculate_voltage()

            if self.voltage <= -65:
                self.state = 'recovering'

        elif self.state == 'recovering':
            #self.p_cal('K')
            self.p_cal('Na')

            decay_rate = 0.5
            self.p_K = 1.0 + (self.p_K - 1.0) * np.exp(-decay_rate * self.dt)
            #here i use the exponential decay, not neccessrily, you can use linear as well
            #p_channel is closing, you can change the rate, or just simple write its closing permeability
            #But in order to make it more realistic, we use the exponential decay
            if self.voltage < -55 and self.Na_h_gate < 1.0:
                self.Na_h_gate += 0.03 * self.dt
                self.Na_h_gate = min(1.0,self.Na_h_gate)

            #self.p_K = max(1.0, self.p_K-1)
            self.voltage = self.calculate_voltage()

            #ions_ok = np.isclose(self.Na_in, 15.0, atol=0.5) and np.isclose(self.K_in, 150.0, atol=1.0)
            pk_ok = self.p_K <= 1.05
            vm_ok = self.voltage<= -65

            if vm_ok and pk_ok:
                self.state = 'resting'
                self.K_channel = False
                self.Na_channel = False
                #self.Na_in = 15.0
                #self.Na_out = 145.0
                #self.K_in = 150.0
                #self.K_out = 5.0
                #self.p_K = 1.0
                #self.p_Na = 0.04
                self.voltage = self.calculate_voltage()


        return self.voltage

    def current_ion_state(self):
        E_Na = self.calculate_eq('Na')
        E_K = self.calculate_eq('K')
        print("====Current_Ion_State====")
        print(f"Na_concentration_in:{self.Na_in:.2f},out:{self.Na_out:.2f}.")
        print(f"K_concentration_in:{self.K_in:.2f},out:{self.K_out:.2f}.")
        print(f"E_K:{E_K:.2f}")
        print(f"E_Na:{E_Na:.2f}")
        print(f"Permeability_K:{self.p_K:.2f}")
        print(f"Permeability_Na:{self.p_Na:.2f}")
        print(f"V_m:{self.calculate_voltage():.2f}")
        print(f"Na_channel:{'Open'if self.Na_channel else 'Close'}")
        print(f"K_channel:{'Open'if self.K_channel else 'Close'}")
        print(f"Na_K_pump:{'Active'if self.Na_K_pump else 'Inactive'}")
        print(f"current_state:{self.state}")
        print("============END=========")



def stimulate_and_plot(sti_str,sti_tinterval,ap_num,duration,sti_dur=1.0,dt=0.01):
    neuron = SimpleNeuron()
    neuron.Na_K_pump = True


    voltages = []
    time = np.arange(0,duration+dt,dt)
    sti_time = [i*sti_tinterval for i in range(1,ap_num+1)]
    aa = 0
    for t in time:
        if (aa<len(sti_time)) and sti_time[aa]<=t<sti_time[aa]+sti_dur:
            neuron.apply_stimulation(sti_str)
        elif (aa<len(sti_time)) and t>sti_time[aa]+sti_dur:
            aa += 1


        v = neuron.update()
        neuron.current_ion_state()
        voltages.append(v)

    plt.figure(figsize=(10,6))
    plt.plot(time,voltages,'b-',linewidth=2)
    plt.show()


stimulate_and_plot(sti_str = 30, sti_tinterval = 50, ap_num = 5, duration = 500)
