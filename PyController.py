from dss import dss
import pandas as pd
from pathlib import Path

# Check the engine version
print(dss.Version)
dss.Plotting.enable()

script_path = Path(__file__).resolve()
node_path = script_path.parent / "8500-Node/1starting.dss"

dss.Text.Command = f"redirect \"{node_path}\""

LoadInformation = []
tempName = []
count = 0
for iload in dss.ActiveCircuit.Loads.AllNames:
    temp = {}
    dss.ActiveCircuit.SetActiveElement(f"Load.{iload}")

    temp["Bus1"] = dss.ActiveCircuit.ActiveElement.Properties("Bus1").Val
    temp["kv"]   = float(dss.ActiveCircuit.ActiveElement.Properties("kv").Val  )
    if "kw" in dss.ActiveCircuit.ActiveElement.AllPropertyNames:
        temp["kw"]   = float(dss.ActiveCircuit.ActiveElement.Properties("kw").Val  )
    else:
        temp["kw"] = 0

    myString = dss.ActiveCircuit.ActiveElement.Properties("kvar").Val.replace("[ ","")
    myString = myString.replace("]","")
    temp["kvar"] = float(myString)

    temp["PVName"] = "PV"+temp["Bus1"]
    temp["kw"] = -1
    tempName.append(temp["PVName"])
    if count > -20: # I used generators origionally and adding 2000 generators was causing the calculations to diverge so this was to limit that, it is an artifact of past times but im leaving just incase i need it
        #dss.Text.Command = f"New   "Generator.{temp["PVName"]}"  Bus1={temp["Bus1"]}  kW=3 PF=1  kVA=3  kV={temp["kv"]}  Xdp=0.27  Xdpp=0.2  H=2 Conn=Delta"
        dss.Text.Command = f'New Load.{temp["PVName"]} Bus1={temp["Bus1"]} Phases=1 Conn=Wye Model=1 kV={temp["kv"]} kW={temp["kw"]}'
        count += 1

    LoadInformation.append(temp)
    p = 1

loadDF = pd.DataFrame(LoadInformation)


dss.ActiveCircuit.Solution.MaxIterations = 300
dss.ActiveCircuit.Solution.MaxControlIterations = 400

dss.Text.Command = f"Solve Number=5"

dss.Text.Command = "Set mode=dynamic h=0.005 number=10"
iterations = 1
steps = 5000
dss.Text.Command = f"Solve Number=1500"
if dss.ActiveCircuit.Solution.Converged == True: # need to check if the "PV" i added cause the program to diverge.
    #dss.Text.Command = "Set mode=dynamic h=0.005 number=10"
    iterations = 1
    #steps = 500
    dss.Text.Command = f"Solve Number={steps*3}"
    
    for i in range(iterations): #cycle power supply attack
        #Turn off the PV loads    
        for index,loadName in loadDF.iterrows():
            name = loadName["PVName"]
            kw   = loadName["kw"]
            dss.Text.Command = f"Edit Load.{name} kW={kw*0.6}"
        dss.Text.Command = f"Solve Number={steps}"
        
        #Turn on the PV loads
        for index,loadName in loadDF.iterrows():
            name = loadName["PVName"]
            kw   = loadName["kw"]
            dss.Text.Command = f"Edit Load.{name} kW={kw*1}"
        dss.Text.Command = f"Solve Number={steps}"
    
    #dss.Text.Command = f"Solve Number={steps/4}"
    
    dss.Plotting.enable(show=False)
    dss.Text.Command = "Plot Circuit Power Max=9000 dots=n labels=n  C1=Blue  1ph=3   ! $00FF0000"
    #dss.Text.Command = "plot circuit Losses Max=50 dots=n labels=n subs=y C1=Blue"
    dss.Text.Command = "plot profile ph=all"
    dss.Text.Command = "Plot monitor object= dpq channel=1"
    dss.Text.Command = "Plot monitor object= G_m1125934_gen"

    dss.Plotting.enable(show=True)
    dss.Text.Command = "plot"
    
    


else:
    print("-------------------")
    print("Simulation diverged")
    print("-------------------")

p = 1
