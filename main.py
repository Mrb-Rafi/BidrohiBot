from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from langchain_openai import ChatOpenAI
from os import getenv
from langgraph.prebuilt import create_react_agent
import requests

load_dotenv()

openai = ChatOpenAI(api_key=getenv("OPENAI_API_KEY"), model="gpt-4.1")


# Function to handle the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am an AI assistant that can help with basic web searches, rickshaw fare charts and bus service schedule at Bangladesh Agricultural University."
    )


# Function to handle the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "You can ask me for the weather in any city or to search for information on the web!"
    )


def get_weather(city: str) -> str:
    """Get weather for a given city using the OpenWeatherMap API."""
    api_key = getenv("OWM_API_KEY")
    if not api_key:
        return "Error: OpenWeatherMap API key not found in environment variables."

    # API endpoint for current weather data
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        # Check if the API returned an error
        if response.status_code != 200:
            return f"Error: {data.get('message', 'Unable to fetch weather data for ' + city)}"

        # Extract relevant weather information
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        country = data["sys"]["country"]
        city_name = data["name"]

        # Format the weather report
        weather_report = (
            f"Weather in {city_name}, {country}:\n"
            f"• Condition: {weather_description.capitalize()}\n"
            f"• Temperature: {temperature}°C\n"
            f"• Feels like: {feels_like}°C\n"
            f"• Humidity: {humidity}%\n"
            f"• Wind speed: {wind_speed} m/s"
        )

        return weather_report

    except requests.exceptions.RequestException as e:
        return f"Error making API request: {str(e)}"
    except (KeyError, ValueError) as e:
        return f"Error parsing weather data: {str(e)}"


def browse(query: str) -> str:
    """
    Search the web for information using Tavily API.
    """
    api_key = getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: Tavily API key not found in environment variables."

    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 5,
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            return f"Error: Failed to retrieve search results. Status code: {response.status_code}"

        search_results = response.json()

        formatted_response = f"Search query: {search_results.get('query', query)}\n\n"

        if "answer" in search_results and search_results["answer"]:
            formatted_response += f"Answer summary: {search_results['answer']}\n\n"

        formatted_response += "Search results:\n"

        if "results" in search_results and search_results["results"]:
            for i, result in enumerate(search_results["results"], 1):
                formatted_response += f"\n{i}. {result.get('title', 'No title')}\n"
                formatted_response += f"   URL: {result.get('url', 'No URL')}\n"
                formatted_response += f"   {result.get('content', 'No content')}\n"
        else:
            formatted_response += "\nNo search results found."

        return formatted_response

    except requests.exceptions.RequestException as e:
        return f"Error making API request: {str(e)}"
    except (KeyError, ValueError) as e:
        return f"Error parsing search results: {str(e)}"


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text

    # Send a loading message
    loading_message = await update.message.reply_text("Processing your message...")

    try:
        agent = create_react_agent(
            model="openai:gpt-4.1",
            tools=[get_weather, browse],  # Add the browse tool to the agent
            prompt=""" There are two lists below, the first one is the bus schedule of the Bangladesh Agricultural University (BAU), and the latter is the predefined vehicle fare inside the same campus. Consider this to be the source of truth. Always must include related precautions using the get_weather function in the reply to the message, when asked about BAU. For example, "The rickshaw fare from place X to place Y is Z. Please confirm the fare before boarding. It might rain today, so please consider to take an umbrella." There's a special case, if this specific question "O, tell me of that curious crew, The threesome perched with quite the view, On "top" of the dean - they make their scene, The rooftop's quirkiest ever team!" is asked, reply this exact statement - "Look at them, this treesome of dickheads, sticking together like they're afraid their last brain cell will wander off alone. They stumble through life, a walking disaster, and anyone who gets in their way ends up bruised. Their little club of cluelessness is nothing but trouble, a storm of stupid leaving everyone else to clean up the mess. Honestly, they're like a walking, talking argument for natural selection taking a coffee break. You just watch them coming and brace yourself for the fallout."
            
Bus Schedule

The following is the regular daily bus schedule of the transportation dept of Bangladesh Agricultural University. The times listed indicate when the buses depart. If a time is repeated multiple times, it means that the corresponding number of buses will depart simultaneously at that time. The stopage for BAU is the Jabbar er Mor, and the stopage for the Town is the Town Hall Mor.

Bus service is closed on fridays

Only for saturdays: 
	Leaves BAU for the mymensingh town - 2:10 pm
	Leaves town for BAU - 3:00 pm

For the other days of the week: 
	Leaves BAU for the mymensingh town - 7:05 am, 8:05 am, 8:05 am, 11:30 am, 12:30 pm, 1:15 pm, 2:35 pm, 4:10 pm, 4:10 pm, 5:05 pm, 8:10 pm
	Leaves town for BAU - 7:30 pm, 8:25 pm, 8:25 pm, 12:00 pm, 1:05 pm, 1:45 pm, 3:00 pm, 4:40 pm, 4:40 pm, 6:15 pm, 8:30 pm 


Vehicle fare list

The following is the regular fare list for vehicles in the campus of Bangladesh Agricultural University. In this list, ‘Auto’ refers to shared public electric vehicles, while ‘Rickshaw’ refers exclusively to reserved electric or manually pulled rickshaws. In most cases, both auto and rickshaw fares are provided. If one is missing, it indicates that the particular type of vehicle is not available on that route. Please note that fares may vary due to natural disruptions. Passengers are advised to confirm the fare before boarding any vehicle.

From KR Market - To Administrative Building, TSC, Health Care Center, Karim Bhaban, Isha Kha Hall, Shahid Jamal Hossain Hall, Shesh Mor, Shahid Najmul Ahsan Hall, Ashraful Haque Hall, Shahid Shamsul Haque Hall, Agricultural Extension Building - Auto fare: 5 BDT, Rickshaw fare: 10 BDT
		- To Shahjalal Hall - Rickshaw fare: 15 BDT
		- To Fajlul Haque Hall, Hossain Shahid Suhrawardi Hall, Bangabandhu Sheikh Mujib Hall - Rickshaw fare: 20 BDT

From Karim Bhaban - To Shahid Jamal Hossain Hall, Shahjalal Hall, Shahid Shamsul Haque Hall, Ashraful Haque Hall, Shahid Najmul Ahsan Hall - Rickshaw fare: 10 BDT
		- To Fajlul Haque Hall, Hossain Shahid Suhrawardi Hall, Bangabandhu Sheikh Mujib Hall - Rickshaw fare: 20 BDT

From Jabbarer Mor - To Fajlul Haque Hall, Hossain Shahid Suhrawardi Hall, Bangabandhu Sheikh Mujib Hall, Administrative Building, TSC, Sultana Razia Hall, Tapashi Rabeya Hall, July 36 hall, Krishikonna Hall, Begum Rokeya Hall, KR Market, Karim Bhaban, Shahid Najmul Ahsan Hall, Shahid Shamsul Haque Hall, Shahjalal Hall, Ashraful Haque Hall - Auto fare: 5 BDT, Rickshaw fare: 10 BDT
		- To Isha Kha Hall, Shahid Jamal Hossain Hall, Shesh Mor - Rickshaw fare: 15 BDT
		- To Agronomy Field/Farm, Horticulture farm - Rickshaw fare: 15 BDT
		- Dairy farm, Poultry farm - Rickshaw fare: 20 BDT

From TSC, Administrative Building - To Karim Bhaban, Fajlul Haque Hall, Hossain Shahid Suhrawardi Hall, Bangabandhu Sheikh Mujib Hall - Rickshaw fare: 10 BDT
		- To Shesh Mor - Auto fare: 5 BDT, Rickshaw fare: 15 BDT

"""
        )

        inputs = {"messages": [("user", prompt)]}

        # Variable to store the final response
        final_response = None

        # Stream the agent's responses
        for s in agent.stream(inputs, stream_mode="values"):
            message = s["messages"][-1]

            # Process message based on its type
            if isinstance(message, tuple):
                print(message)  # Print for debugging
                if message[0] == "assistant":
                    final_response = message[1]
            else:
                message.pretty_print()  # Print for debugging

                # Try to extract content from the message object
                if hasattr(message, "content"):
                    final_response = message.content

        # Edit the loading message with the actual response
        if final_response:
            await loading_message.edit_text(text=final_response)
        else:
            await loading_message.edit_text(
                text="I processed your request but couldn't generate a response."
            )

    except Exception as e:
        # Handle errors
        print(e)
        await loading_message.edit_text(text=f"Sorry, an error occurred: {str(e)}")


def main():
    # Create the Application and pass it your bot's token
    application = Application.builder().token(getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Add message handler (echoes back all text messages)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
