
from mcp.server.fastmcp import FastMCP
from common.db import query

mcp = FastMCP(
    "Flights",
    host="127.0.0.1",
    port=8001
)

ALIASES = {
    "banglore": "bengaluru",
    "bangalore": "bengaluru",
    "bombay": "mumbai",
    "new delhi": "delhi",
    "madaras": "chennai",
    "culcutta": "kolkata"
}


def clean(city: str) -> str:
    city = city.strip().lower()
    return ALIASES.get(city, city)


@mcp.tool()
def search_flight(
    origin: str,
    destination: str,
    date: str = ""
) -> list[dict]:
    """Search flights between two cities, sorted by price.
    Optional date format: YYYY-MM-DD.
    """

    sql = """
        SELECT id, flight_no, airline, origin, destination,
               depart_date, depart_time, arrive_time,
               price, seats_available
        FROM flights
        WHERE LOWER(origin) = ?
          AND LOWER(destination) = ?
          AND seats_available > 0
    """

    params = [clean(origin), clean(destination)]

    if date:
        sql += " AND depart_date = ?"
        params.append(date)

    sql += " ORDER BY price ASC LIMIT 5"

    return query(sql, params)


@mcp.tool()
def get_flight(flight_id: int) -> dict:
    """Get complete details of a flight using its ID."""

    rows = query(
        "SELECT * FROM flights WHERE id = ?",
        (flight_id,)
    )

    if rows:
        return rows[0]

    return {"error": f"No flight with id {flight_id}"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")