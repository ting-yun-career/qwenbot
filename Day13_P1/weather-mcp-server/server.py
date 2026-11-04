from fastmcp import FastMCP


mcp = FastMCP("Weather Server")


@mcp.tool()
def get_weather(city: str):
    """
    Return weather information for a city.
    """

    weather_data = {
        "Delhi": "Sunny, 32°C",
        "Paris": "Cloudy, 9°C",
        "Sydney": "Rainy, 29°C",
        "London": "Partly cloudy, 15°C"}

    return weather_data.get(
        city,
        "Weather data not available."
    )


if __name__ == "__main__":
    print(
        "Starting Weather MCP Server..."
    )

    mcp.run()
