# The Randis Shop

Games and apps made with [Randis UDS](https://github.com/RandyWilliamMoore/randis-uds) by Randy Moore. Support: https://ko-fi.com/moorescombinatoricsmatrix

**[Open The Randis Shop](https://randywilliammoore.github.io/randis-shop/)**

![Randis UDS with three tabs open: a notepad, Randis Paint, and the Randis Shop tab listing the shop's games](site/screens/randis-uds.png)

Each item is one folder under `games/` or `apps/`. Randis UDS itself, a download rather than a page that plays here, is `software/randis-uds/`. Run `python tools/build_index.py` after changing one.

## The Jukebox

Songs made with Randis Sound Forge, free to play here and to download, royalty free: use them in anything, paid work included, with no payment or sign-up. The one thing you can't do is sell or hand out the songs themselves as your own music. A credit is welcome, never required.

Each song is one folder under `music/`. To add one:

```powershell
python tools/add_music.py "C:/path/My Song.wav" --name "My Song" --genre "Elevator Music" --blurb "Soft piano for a hotel lobby."
```

## Tests

They run the real shop page in a real browser window (Edge WebView2, through pywebview), on Windows, from a test server on this computer. The window opens off screen.

```powershell
pip install pywebview
python tests/ship_test.py       # every item: listed, logo, page, Play opens the walled player, runs under its rules, every first-screen button
python tests/security_test.py   # a hostile test game tries to get out of the player; then every item still opens
python tests/link_test.py       # outside links ask first, and only "Open it" opens one
python tests/save_test.py       # files a game makes are saved by the shop page: known kinds only, one at a time
python tests/play_test.py       # real rounds of the games that have a play check
python tests/music_test.py      # Sound Forge makes elevator music; add_music.py; the Jukebox plays and hands out songs
```

`ship_test.py` and `play_test.py` take item names to test only those, like `python tests/ship_test.py dice-master`. Run all six before pushing a change to `site/`, `index.html` or `site.js`; run `ship_test.py` on any item you add or change.
