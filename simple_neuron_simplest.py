import matplotlib.pyplot as plt
import numpy as np

class SimpleNeuron():


    """This is a simple neuron action potential simulation. """

    def __init__(self): #all of the parameters based on real bio(i am trying to modify but i have no idea how to make it better)
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
        self.Na_h_gate = 1.0

        #permeability
        self.p_Na = 0.04
        self.p_K = 1.0

        #C
        self.RT_F = 58.0
        self.EPS = 1e-6 #avoid log error

        self.voltage = self.caculate_voltage()



    def caculate_eq(self,ion): #use Nernst equation
        if ion == 'Na':
            E_Na = self.RT_F*np.log10(self.Na_out/self.Na_in)
            return E_Na
        elif ion == 'K':
            E_K = self.RT_F*np.log10(self.K_out/self.K_in)
            return E_K

    def caculate_voltage(self): #use Goldman equation
        nume = self.p_K*self.K_out + self.p_Na*self.Na_out
        denom = self.p_K*self.K_in + self.p_Na*self.Na_in

        V_m = self.RT_F*np.log10(nume / denom)

        return V_m


    def pump_cycle(self,dt=0.1):
        #Here is the pump, noticed that there are some problems due to the parameters, so when you close it, the change will not be noticed immediately, i'm trying to fix it
        if self.Na_K_pump:
            self.Na_in = max(self.EPS, self.Na_in-0.03*dt) #here the changing parameters based on real biology
            self.Na_out = max(self.EPS, self.Na_out+0.03*dt)
            self.K_in = max(self.EPS, self.K_in+0.02*dt)
            self.K_out= max(self.EPS, self.K_out-0.02*dt)

    def can_stimulate(self):
        return self.Na_h_gate>0.8 and self.state=='resting'
        #when h_gate almost recover(the protein removed) and state in resting

    def apply_stimulation(self,strength): #recieve the stimulation will change the voltage
        #self.strength = float(strength)
        if self.can_stimulate():
            self.p_Na += strength*0.01 #linear increase the p_Na(can be changed to exponential increasing)
            self.voltage = self.caculate_voltage()

            if self.voltage >= -40:
                self.state = 'depolarizing'

    def update(self,dt=0.1): #update voltage by time/step(stimulate the raising pharse when sodium channels open)

        self.pump_cycle(dt) #background working


        if self.state == 'resting':

            if self.Na_h_gate<1.0:
                #h gate recovering
                self.Na_h_gate += 0.05*dt
                self.Na_h_gate = min(1.0, self.Na_h_gate)

            self.voltage = self.caculate_voltage()


        elif self.state == 'depolarizing':
            self.Na_channel = True
            #h gate is closing
            self.Na_h_gate = max(0.0, self.Na_h_gate - 0.4 * dt)

            #self.p_Na = min(20.0, self.p_Na + 20.0*dt) #Na_m_gate open p_Na raise rapidly
            self.p_Na = 7
            self.p_K = 1.0

            self.Na_in = max(self.EPS, self.Na_in+ 0.05*dt)
            self.Na_out = max(self.EPS, self.Na_out- 0.05*dt)

            self.voltage = self.caculate_voltage()

            if self.voltage >= 30 or self.Na_h_gate<0.2:
                self.state = 'repolarizing'
                self.Na_channel = False
                self.K_channel  = True
                self.p_Na = 0.04
                #self.p_K  = 2

        elif self.state == 'repolarizing':
            self.Na_channel = False
            self.K_channel = True
            self.p_Na = 0.04 #m_gate close rapidly, here i just simply change to the closing permeability
            #if you want you can use exponential decay with a greater rate
            #self.p_K = min(20.0, self.p_K + 30.0*dt)
            self.p_K = 3

            if self.Na_h_gate < 1.0:
                self.Na_h_gate += 0.02 * dt

            self.K_out = max(self.EPS, self.K_out+0.05*dt)
            self.K_in = max(self.EPS, self.K_in-0.05*dt)

            self.voltage = self.caculate_voltage()

            if self.voltage <= -75:
                self.state = 'recovering'

        elif self.state == 'recovering':
            decay_rate = 10
            self.p_K = 1.0 + (self.p_K - 1.0) * np.exp(-decay_rate * dt)
            #here i use the first ordered relaxtion, not neccessrily, you can use linear as well
            #p_channel is closing, you can change the rate, or just simple write its closing permeability
            #But in order to make it more realistic, we use the exponential decay

            if self.Na_h_gate < 1.0:
                self.Na_h_gate += 0.03 * dt
                self.Na_h_gate = min(1.0,self.Na_h_gate)

            #self.p_K = max(1.0, self.p_K-1)
            self.voltage = self.caculate_voltage()

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
                self.p_K = 1.0
                self.p_Na = 0.04
                self.voltage = self.caculate_voltage()


        return self.voltage

    def current_ion_state(self):
        E_Na = self.caculate_eq('Na')
        E_K = self.caculate_eq('K')
        print("====Current_Ion_State====")
        print(f"Na_concentration_in:{self.Na_in:.2f},out:{self.Na_out:.2f}.")
        print(f"K_concentration_in:{self.K_in:.2f},out:{self.K_out:.2f}.")
        print(f"E_K:{E_K:.2f}")
        print(f"E_Na:{E_Na:.2f}")
        print(f"Permeability_K:{self.p_K}")
        print(f"Permeability_Na:{self.p_Na}")
        print(f"V_m:{self.caculate_voltage():.2f}")
        print(f"Na_channel:{'Open'if self.Na_channel else 'Close'}")
        print(f"K_channel:{'Open'if self.K_channel else 'Close'}")
        print(f"Na_K_pump:{'Active'if self.Na_K_pump else 'Inactive'}")
        print(f"current_state:{self.state}")
        print("============END=========")



def stimulate_and_plot(sti_str,sti_tinterval,ap_num,duration,dt=0.1):
    neuron = SimpleNeuron()
    neuron.Na_K_pump = True


    voltages = []
    time = np.arange(0,duration+dt,dt)
    sti_time = [i*sti_tinterval for i in range(1,ap_num+1)]
    aa = 0
    for t in time:
        if (aa<len(sti_time)) and (np.isclose(t,sti_time[aa])):
            neuron.apply_stimulation(sti_str)
            aa += 1


        v = neuron.update()
        neuron.current_ion_state()
        voltages.append(v)

    plt.figure(figsize=(10,6))
    plt.plot(time,voltages,'b-',linewidth=2)
    plt.show()


stimulate_and_plot(70,3,5,20)
