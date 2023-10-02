import requests
import pyjson5
from datetime import datetime
import os
import difflib
from colorama import Fore, Style, init

# Initialize colorama
init()
print("Loading/Downloading Data")
os.makedirs("stats",exist_ok=True)
# Load Items
if os.path.exists("stats/items.json"):
    with open('stats/items.json', 'r') as file:
        itemRaw = file.read()
    itemData = pyjson5.loads(itemRaw)
else:
    url = 'https://play.pokemonshowdown.com/data/items.js'
    itemJS = requests.get(url).text
    itemRaw = "{"+itemJS.split("{",1)[1][:-1]
    with open('stats/items.json', 'w', encoding="utf-8") as file:
        file.write(itemRaw)
    itemData = pyjson5.loads(itemRaw)


# Load Abilities
if os.path.exists("stats/abilities.json"):
    with open('stats/abilities.json', 'r', encoding="utf8") as file:
        abilitiesRaw = file.read()
    abilitiesData = pyjson5.loads(abilitiesRaw)
else:
    url = 'https://play.pokemonshowdown.com/data/abilities.js'
    abilitiesJS = requests.get(url).text
    abilitiesRaw = "{"+abilitiesJS.split("{",1)[1][:-1]
    with open('stats/abilities.json', 'w', encoding="utf-8") as file:
        file.write(abilitiesRaw)
    abilitiesData = pyjson5.loads(abilitiesRaw)

# Load Moves
if os.path.exists("stats/moves.json"):
    with open('stats/moves.json', 'r', encoding="utf8") as file:
        movesRaw = file.read()
    movesData = pyjson5.loads(movesRaw)
else:
    url = 'https://play.pokemonshowdown.com/data/moves.json'
    movesRaw = requests.get(url).text
    with open('stats/moves.json', 'w', encoding="utf-8") as file:
        file.write(movesRaw)
    movesData = pyjson5.loads(movesRaw)

# Load Pokedex (unused for now)
if os.path.exists("stats/pokedex.json"):
    with open('stats/pokedex.json', 'r', encoding="utf8") as file:
        pokedexRaw = file.read()
    pokedexData = pyjson5.loads(pokedexRaw)
else:
    url = 'https://play.pokemonshowdown.com/data/pokedex.json'
    pokedexRaw = requests.get(url).text
    with open('stats/pokedex.json', 'w', encoding="utf-8") as file:
        file.write(pokedexRaw)
    pokedexData = pyjson5.loads(pokedexRaw)

year = datetime.now().year
month = datetime.now().month-1
if month==0:
    month = 12
    year = year-1
month = str(month).zfill(2)
year = str(year)
meta = "gen9vgc2023regulatione"
rating = "0"
if os.path.exists(f"stats/{year}-{month}-{meta}-{rating}.json"):
    with open(f'stats/{year}-{month}-{meta}-{rating}.json', 'r', encoding="utf8") as file:
        statsRaw = file.read()
    statsData = pyjson5.loads(statsRaw)
else:
    urls = [f'https://www.smogon.com/stats/{year}-{month}/chaos/{meta}-{rating}.json',
            f'https://www.smogon.com/stats/{year}-{month}-DLC1/chaos/{meta}-{rating}.json',
            f'https://www.smogon.com/stats/{year}-{month}-DLC2/chaos/{meta}-{rating}.json',
            f'https://www.smogon.com/stats/{year}-{month}-H1/chaos/{meta}-{rating}.json',
            f'https://www.smogon.com/stats/{year}-{month}-H2/chaos/{meta}-{rating}.json',
            ]
    for url in urls:
        try: 
            response = requests.get(url)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException:
            print(f"Failed to get data from {url}")
    else:
        print("All URLs failed. Uh oh. Stinky.")
    statsRaw = response.text
    statsData = pyjson5.loads(statsRaw)
    with open(f'stats/{year}-{month}-{meta}-{rating}.json', 'w', encoding="utf-8") as file:
        file.write(statsRaw)

info = statsData["info"]
data = statsData["data"]
metagame = info["metagame"]
pokemon = data.keys()


#Oranized from most used to least
pokemon_ordered = sorted(pokemon, key=lambda x: data[x]["Raw count"], reverse=True)

def getStats(poke,category):
    dataPokemon = data[poke][category]
    catSorted = sorted(dataPokemon.keys(), key=lambda x: dataPokemon[x], reverse=True)
    return catSorted

def printTopData(poke,category,count=10):
    sorted = getStats(poke,category)
    print(f"{Fore.GREEN}---Top {count} {category} for {poke}---{Fore.RESET}")
    rawCount = data[poke]["Raw count"]
    for i in range(count):
        try:
            key = sorted[i]
        except IndexError:
            return
        use = data[poke][category][key]/rawCount*100
        use = round(use,3)
        if key == "":
            key = "nothing"
        if category=="Moves" and key!="nothing":
            key = movesData[key]["name"]

        if category=="Abilities" and key!="nothing":
            key = abilitiesData[key]["name"]

        if category=="Items" and key!="nothing":
            key = itemData[key]["name"]
        
        print(f"{Fore.CYAN}{key}{Fore.RESET} : {Fore.YELLOW}{use}%{Fore.RESET}")
    
def allDataPokemon(poke):
    word = poke.lower()
    possibilities = pokemon
    normalized_possibilities = {p.lower(): p for p in possibilities}
    result = difflib.get_close_matches(word, normalized_possibilities.keys(),10)
    normalized_result = [normalized_possibilities[r] for r in result]
    if len(normalized_result)>0:
        close = normalized_result[0]
        pokeSearch = close
    else:
        print(f"{Fore.RED}No Data on {poke}{Fore.RESET}")
        return
    try:
        rank = pokemon_ordered.index(pokeSearch)+1
    except ValueError:
        print(f"{Fore.RED}No Data on {poke}{Fore.RESET}")
        return
    usage = data[pokeSearch]["usage"] *100
    usage = round(usage,2)
    print(f"\nData for {Fore.GREEN}{pokeSearch}{Fore.RESET} with Monthly Rank of {rank} and Usage of {usage}%")
    printTopData(pokeSearch,"Moves")
    print("")
    printTopData(pokeSearch,"Items")
    print("")
    printTopData(pokeSearch,"Abilities",3)
    print("")
    printTopData(pokeSearch,"Spreads")
    print("")
    printTopData(pokeSearch,"Teammates")

# 'usage', 'Checks and Counters', 'Viability Ceiling', 'Raw count'


# 'Moves', 'Abilities', 'Teammates', 'Items', 'Spreads', 'Happiness'

for i in range(100):
    pkm = pokemon_ordered[i]
    use = data[pkm]["usage"] *100
    use = round(use,2)
    print(f"Rank {i+1}: {Fore.YELLOW}{pkm}{Fore.RESET}, Usage Percent: {use}%")

while True:
    user_input = input(f"{Fore.GREEN}Search {Fore.YELLOW}Pokemon{Fore.GREEN} (or '{Fore.YELLOW}q{Fore.GREEN}' to quit): {Fore.RESET}")

    if user_input == 'q':
        break  # Exit the loop if the user types 'q'
    
    allDataPokemon(user_input)
