# Matchday TV Guide

See which TV channel shows each match today, tomorrow or on any date, with live scores.
Football first, with handball, tennis, basketball and ice hockey tabs built in.

**Live app:** https://adkk77.github.io/matchday-tv-guide/

## How it works
- Single static page (`index.html`), no build step, hosted on GitHub Pages.
- Data comes from [TheSportsDB](https://www.thesportsdb.com) straight from the browser:
  `eventsday.php` (fixtures + scores) and `eventstv.php` (TV channels by country).
- Uses the free key `123` by default. Enter a premium key under **Data source** for full listings and minute-by-minute live scores (v2 `livescore`).
- Today's view refreshes every minute. If the feed can't be reached, the app shows example data and says so.
- Installable on a phone ("Add to Home Screen").

## Adding a sport
Add an entry to the `SPORTS` array in `index.html` (`id` is TheSportsDB's sport name).
