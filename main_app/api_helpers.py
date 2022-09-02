from dotenv import load_dotenv
from datetime import datetime, timezone
import requests
import csv

from requests.structures import CaseInsensitiveDict

# print(animal_breeds)
out_array = []
name = 'Cat'
breeds = animal_breeds['breeds']
for breed in breeds:
  new_row = [name, breed['name']]
  out_array.append(new_row)

# print(out_array)

# with open('main_app/static/colors.csv', 'w') as csvfile:
    
#     data = out_array
#     f.write(data)



# with open('main_app/static/breeds.csv', 'a') as csvfile: 
#     # creating a csv writer object 
#     csvwriter = csv.writer(csvfile) 
#     csvwriter.writerows(out_array)



