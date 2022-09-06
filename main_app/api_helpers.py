from dotenv import load_dotenv
from datetime import datetime, timezone
import requests
import csv

from requests.structures import CaseInsensitiveDict

# # print(animal_breeds)
# out_array = []
# name = 'Cat'
# # breeds = animal_breeds['breeds']
# for breed in breeds:
#   new_row = [name, breed['name']]
#   out_array.append(new_row)

# print(out_array)

# with open('main_app/static/colors.csv', 'w') as csvfile:
    
#     data = out_array
#     f.write(data)



# with open('main_app/static/breeds.csv', 'a') as csvfile: 
#     # creating a csv writer object 
#     csvwriter = csv.writer(csvfile) 
#     csvwriter.writerows(out_array)

import json

class Favorite:
    def __init__(self, id, name, gender, age, breed):
        self.id = id
        self.name = name
        self.gender = gender
        self.age = age
        self.breed = breed

    @classmethod
    def from_json(cls, json_string):
        json_dict = json.loads(json_string)
        return Favorite(**json_dict)

    def __repr__(self):
        return f'<Favorite { self.name }, {self.gender} { self.breed }>'

json_string = '''{
    "id": "123",
    "name": "Ace",
    "gender": "Male",
    "age": "1",
    "breed": "Sphinx"
}'''

favorite = Favorite.from_json(json_string)

print(favorite)
print(favorite.gender)