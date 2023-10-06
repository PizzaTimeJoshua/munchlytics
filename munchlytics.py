import requests
import pyjson5
from datetime import datetime
import os
import difflib
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

# Initialize colorama
init()
print("Loading/Downloading Data")
os.makedirs("stats",exist_ok=True)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def loadFiles():
    global itemData, movesData, abilitiesData
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

def loadStats(meta,month,year,rating,tryLastMonth=True):
    global data, pokemon, pokemon_ordered, statsData
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
                print(f"Got data from {url}")
                break
            except requests.exceptions.RequestException:
                print(f"Failed to get data from {url}")
        else:
            print("All URLs failed.")
            #Tries the month before if anything goes wrong
            if tryLastMonth:
                print("Trying month prior.")
                oldMonth = int(month)-1
                oldYear = int(year)
                if oldMonth==0:
                    oldMonth = 12
                    oldYear=oldYear-1
                oldMonth = str(oldMonth).zfill(2)
                oldYear = str(oldYear)
                loadStats(meta,oldMonth,oldYear,rating,False)
            return
        statsRaw = response.text
        statsData = pyjson5.loads(statsRaw)
        with open(f'stats/{year}-{month}-{meta}-{rating}.json', 'w', encoding="utf-8") as file:
            file.write(statsRaw)
    data = statsData["data"]
    pokemon = data.keys()
    pokemon_ordered = sorted(pokemon, key=lambda x: data[x]["usage"], reverse=True)

def getStats(poke,category):
    if category=="Natures":
        dataPokemon = {}
        for spread in data[poke]["Spreads"]:
            nature = spread.split(':')[0]
            weight = data[poke]["Spreads"][spread]
            dataPokemon[nature] = dataPokemon.get(nature,0) + weight

    else:
        dataPokemon = data[poke][category]
    if category=="Checks and Counters":
        filtered_counters = {key: value for key, value in dataPokemon.items() if (value[2] < 0.01 and value[1] > 0.5)}
        catSorted = sorted(filtered_counters.keys(), key=lambda x: filtered_counters[x][1], reverse=True)
        return catSorted, dataPokemon
    catSorted = sorted(dataPokemon.keys(), key=lambda x: dataPokemon[x], reverse=True)
    return catSorted, dataPokemon

def printTopData(poke,category,count=10):
    sorted , dataPokemon = getStats(poke,category)
    totalCount = sum(list(data[poke]["Abilities"].values()))
    totalVals = min(len(sorted),count)
    if totalVals==0:
        # If No Data, don't show (Usually for Checks and Counters)
        return
    print(f"{Fore.GREEN}---Top {totalVals} {category} for {poke}---{Fore.RESET}")
    for i in range(totalVals):
        try:
            key = sorted[i]
        except IndexError:
            return
        if category=="Checks and Counters":
            use = dataPokemon[key][1]*100
        else:
            use = dataPokemon[key]/totalCount*100
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
    print(f"For the metagame: {Fore.GREEN}{meta}{Fore.RESET} with a threshold of {Fore.GREEN}{rating}{Fore.RESET}\n")
    printTopData(pokeSearch,"Moves")
    print("")
    printTopData(pokeSearch,"Items")
    print("")
    printTopData(pokeSearch,"Abilities",3)
    print("")
    printTopData(pokeSearch,"Spreads")
    print("")
    printTopData(pokeSearch,"Natures",5)
    print("")
    printTopData(pokeSearch,"Teammates")
    print("")
    printTopData(pokeSearch,"Checks and Counters")

def showTopPokemon(top=100):
    print(f"{Fore.CYAN}Top {top} Pokemon of {Fore.YELLOW}{meta}{Fore.CYAN} with a threshold of {Fore.YELLOW}{rating}{Fore.RESET}")
    for i in range(top):
        try:
            pkm = pokemon_ordered[i]
        except IndexError:
            break
        use = data[pkm]["usage"] *100
        use = round(use,2)
        print(f"Rank {i+1}: {Fore.YELLOW}{pkm}{Fore.RESET}, Usage Percent: {use}%")
def getMetagames():
    urls = [f'https://www.smogon.com/stats/{year}-{month}/chaos/',
            f'https://www.smogon.com/stats/{year}-{month}-DLC1/chaos/',
            f'https://www.smogon.com/stats/{year}-{month}-DLC2/chaos/',
            f'https://www.smogon.com/stats/{year}-{month}-H1/chaos/',
            f'https://www.smogon.com/stats/{year}-{month}-H2/chaos/',
            ]
    formats = []
    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if (".json" in href):
                    form = href.split("-",1)[0]
                    formats.append(form)  
            formats = list(set(formats))
            break
    else:
        print("Unable to obtain metagames.")
    return(formats)
    
def saveSettings():
    config = {
        "meta": meta,
        "rating": rating
    }
    with open("config.json","w") as file:
        file.write(str(config))

def loadSettings():
    global meta, rating
    if os.path.exists("config.json"):
        with open('config.json', 'r') as file:
            config = pyjson5.load(file)
        meta = config["meta"]
        rating = config["rating"]
    else:
        saveSettings()

def changeSettings():
    print(f"{Fore.YELLOW}1{Fore.GREEN} to change {Fore.YELLOW}metagame{Fore.GREEN}{Fore.RESET}")
    print(f"{Fore.YELLOW}2{Fore.GREEN} to change {Fore.YELLOW}cutoff rating threshold{Fore.GREEN}{Fore.RESET}")
    print(f"{Fore.YELLOW}3{Fore.GREEN} to {Fore.YELLOW}Update Moves/Abilities/Items (if new DLC dropped){Fore.GREEN}{Fore.RESET}")
    print(f"{Fore.YELLOW}4{Fore.GREEN} to {Fore.RED}Cancel{Fore.GREEN}{Fore.RESET}")
    user_input = input(f"{Fore.CYAN}Input:{Fore.RESET} ")
    global rating, meta
    if user_input=='1':
        print(f"{Fore.CYAN}Type metagame would you like to load. Will autocorrect to closest match.{Fore.RESET}")
        print(f"{Fore.CYAN}e.g. {Fore.YELLOW}gen9anythinggoes, gen9vgc2023regulatione, gen1ou{Fore.RESET}")
        user_input = input()
        metagames = getMetagames()
        word = user_input.lower()
        possibilities = metagames
        normalized_possibilities = {p.lower(): p for p in possibilities}
        result = difflib.get_close_matches(word, normalized_possibilities.keys(),10)
        normalized_result = [normalized_possibilities[r] for r in result]
        if len(normalized_result)>0:
            close = normalized_result[0]
            possibleMeta = close
            user_input = input(f"{Fore.CYAN}Is {Fore.YELLOW}{possibleMeta}{Fore.CYAN} the metagame you want to load? (Y/N):{Fore.RESET} ")
            if user_input.lower()=='y' or user_input.lower()=='yes' or user_input.lower()=='':
                meta = possibleMeta
                saveSettings()
                loadStats(meta,month,year,rating)
        else:
            print(f"{Fore.RED}Error: {Fore.YELLOW}{user_input}{Fore.RED} did not match any metagames.{Fore.RESET}")
            changeSettings()
    elif user_input=='2':
        user_input = input(f"{Fore.CYAN}Please type either: {Fore.YELLOW}0, 1500, 1630, or 1760:{Fore.RESET} ")
        if user_input=="0" or user_input=="1500" or user_input=="1630" or user_input=="1760":
            rating=user_input
            saveSettings()
            loadStats(meta,month,year,rating)
        else:
            print(f"{Fore.RED}Unknown Value. Cancelled.{Fore.RESET}")
            changeSettings()
    elif user_input=='3':
        if os.path.exists("stats/items.json"):
            os.remove("stats/items.json")
            print("Deleted: stats/items.json")

        if os.path.exists("stats/abilities.json"):
            os.remove("stats/abilities.json")
            print("Deleted: stats/abilities.json")

        if os.path.exists("stats/moves.json"):
            os.remove("stats/moves.json")
            print("Deleted: stats/moves.json")

        if os.path.exists("stats/pokedex.json"):
            os.remove("stats/pokedex.json")
            print("Deleted: stats/pokedex.json")
        print("Redownloading...")
        loadFiles()
    elif user_input=='4':
        pass
    else:
        changeSettings()


#==========Settings==========#
global meta, year, month, rating
year = datetime.now().year
month = datetime.now().month-1
if month==0:
    month = 12
    year = year-1
month = str(month).zfill(2)
year = str(year)
topPokemon=100
# Default
meta = "gen9vgc2023regulatione"
rating = "1760"
loadSettings()
#============================#

loadFiles()
loadStats(meta,month,year,rating)
showTopPokemon(topPokemon)
while True:
    user_input = input(f"{Fore.GREEN}Search {Fore.YELLOW}Pokemon{Fore.GREEN} (or '{Fore.YELLOW}1{Fore.GREEN}' for Settings): {Fore.RESET}")

    if user_input == '1':
        clear_console()
        changeSettings()
        showTopPokemon(topPokemon)
    else:
        allDataPokemon(user_input)
