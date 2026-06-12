#%% 
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('res_2024.csv')

#%%
plt.plot(df['voltage'])