# LoL-dataset-generator
League of Legends dataset generator with statistics of several players in different games.

# Usage
1. [Create Riot Games account](https://authenticate.riotgames.com/?client_id=riot-developer-portal&locale=en_US&method=riot_identity&platform=web&redirect_uri=https%3A%2F%2Fauth.riotgames.com%2Fauthorize%3Fclient_id%3Driot-developer-portal%26prompt%3Dsignup%26redirect_uri%3Dhttps%253A%252F%252Fdeveloper.riotgames.com%252Foauth2-callback%26response_type%3Dcode%26scope%3Dopenid%2520email%2520summoner%26ui_locales%3Den)
2. [Get a development API key](https://developer.riotgames.com/)
3. Create `.env` file at the root of the project and add your API key like this:

```env
RIOT_API_KEY = <YOUR_API_KEY>
```

4. Run the script `dataset-generator.py`:
```python
python3 dataset-generator.py
```
