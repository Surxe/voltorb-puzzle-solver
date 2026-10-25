// Voltorb Flip solver UI. The server is stateless: every submit sends the counters plus all flip results so far.
(() => {
  'use strict';

  const app = document.getElementById('app');
  const SIZE = Number(app.dataset.size);
  const sprite = (name) => `${app.dataset.sprites}${name}.png`;
  const FACES = ['card_0', 'card_1', 'card_2', 'card_3']; // by card value, 0 being a Voltorb
  for (const name of FACES) new Image().src = sprite(name); // so a typed flip shows its face at once
  const TOTAL_KEY = 'voltorb-solver-total-coins';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const grid = (make) => Array.from({ length: SIZE }, (_, i) => Array.from({ length: SIZE }, (_, j) => make(i, j)));

  const message = $('#message');
  const levelInput = $('#level');
  const tiles = grid((i, j) => $(`.tile[data-i="${i}"][data-j="${j}"]`));
  const allTiles = tiles.flat();
  const counters = (line) => Array.from({ length: SIZE }, (_, n) => ({
    value: $(`.count.value[data-line="${line}"][data-n="${n}"]`),
    voltorbs: $(`.count.voltorbs[data-line="${line}"][data-n="${n}"]`),
  }));
  const rows = counters('row');
  const cols = counters('col');
  const actionButtons = $$('.action');

  let revealed = grid(() => null); // flip results the solver has accepted
  let history = []; // `revealed` before each accepted batch, for Back
  let phase = 'counts'; // counts -> flip -> over
  let overByDone = false; // the round ended because the player said every 2 and 3 was found
  let banked = 0; // this round's coins already added to the total
  let lastResponse = null;
  let busy = false;

  function drawCoins(id, coins) {
    $(`#${id}`).textContent = String(Math.max(0, Math.min(coins, 99999))).padStart(5, '0');
  }

  // ---------- inputs ----------

  // Keeps only what a field can hold, clamping to its range by falling back to the last digit typed
  function sanitize(input, max) {
    let text = input.value.replace(/\D/g, '');
    if (text !== '' && Number(text) > max) text = text.slice(-1);
    if (text !== '' && Number(text) > max) text = '';
    if (text.length > 1) text = String(Number(text)); // "05" -> "5"
    input.value = text;
  }

  for (const { value, voltorbs } of [...rows, ...cols]) {
    value.addEventListener('input', () => sanitize(value, 3 * SIZE));
    voltorbs.addEventListener('input', () => sanitize(voltorbs, SIZE));
  }
  levelInput.addEventListener('input', () => {
    sanitize(levelInput, 8);
    if (levelInput.value === '0') levelInput.value = '';
  });
  $$('input').forEach((input) => input.addEventListener('focus', () => input.select()));

  const flipInput = (tile) => $('.flip', tile);
  const face = (tile) => $('.face', tile);
  const position = (tile) => [Number(tile.dataset.i), Number(tile.dataset.j)];

  for (const tile of allTiles) {
    const input = flipInput(tile);
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^0-3]/g, '').slice(-1);
      preview(tile);
    });
    tile.addEventListener('click', () => {
      if (phase !== 'flip' || busy || tile.classList.contains('revealed')) return;
      if (!tile.classList.contains('pending')) {
        setPending(tile, true);
        tile.classList.add('manual');
      }
      input.focus();
    });
  }

  function preview(tile) {
    const value = flipInput(tile).value;
    tile.classList.toggle('previewing', value !== '');
    if (value !== '') face(tile).src = sprite(FACES[Number(value)]);
    else if (!tile.classList.contains('revealed')) face(tile).src = sprite('card_back');
  }

  function setPending(tile, pending) {
    const input = flipInput(tile);
    tile.classList.toggle('pending', pending);
    tile.classList.remove('manual');
    input.disabled = !pending;
    input.value = '';
    preview(tile);
  }

  const pendingTiles = () => allTiles.filter((tile) => tile.classList.contains('pending'));

  // ---------- messages and menu ----------

  function say(text, focus) {
    message.textContent = text;
    if (focus) focus.focus();
  }

  function setMenu(actions) {
    actionButtons.forEach((button, k) => {
      const action = actions[k];
      button.disabled = !action; // an empty row stays drawn, like the game's menu
      button.onclick = action ? () => { if (!busy) action.run(); } : null;
      button.textContent = action ? action.label : '';
      button.title = action?.title ?? '';
    });
  }

  // a chance that's only nearly certain shouldn't round to one that is
  const percent = (p) => (p > 0 && p < 0.005 ? '<1%' : p < 1 && p > 0.995 ? '>99%' : `${Math.round(p * 100)}%`);
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

  // ---------- total coins, kept per browser ----------

  let totalCoins = 0;
  try { totalCoins = Number(localStorage.getItem(TOTAL_KEY)) || 0; } catch { /* storage unavailable */ }

  function addToTotal(coins) {
    totalCoins += coins;
    try { localStorage.setItem(TOTAL_KEY, String(totalCoins)); } catch { /* kept for this page only */ }
    drawCoins('total-coins', totalCoins);
  }
  function bank(coins) {
    banked = coins;
    addToTotal(coins);
  }
  function unbank() {
    addToTotal(-banked);
    banked = 0;
  }

  // ---------- phases ----------

  class InputError extends Error {
    constructor(text, input) { super(text); this.input = input; }
  }

  function readCounts(lines, name) {
    return lines.map(({ value, voltorbs }, n) => {
      if (value.value === '') throw new InputError(`Enter ${name} ${n + 1}'s points.`, value);
      if (voltorbs.value === '') throw new InputError(`Enter ${name} ${n + 1}'s Voltorbs.`, voltorbs);
      return [Number(value.value), Number(voltorbs.value)];
    });
  }

  async function solve(nextRevealed) {
    let counts;
    try {
      counts = { rows: readCounts(rows, 'row'), cols: readCounts(cols, 'column') };
    } catch (error) {
      if (error instanceof InputError) return say(error.message, error.input);
      throw error;
    }
    setBusy(true);
    try {
      let reply, response;
      try {
        reply = await fetch('api/solve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...counts, revealed: nextRevealed, level: levelInput.value ? Number(levelInput.value) : null }),
        });
        response = await reply.json();
      } catch (error) {
        return say(`Couldn't reach the solver: ${error.message}`);
      }
      if (reply.status === 422) {
        return say('No board fits these counters and flips.\nCheck them for a typo.');
      }
      if (response.error) {
        return say(`Couldn't solve: ${response.error}`);
      }
      if (nextRevealed !== revealed) {
        history.push(revealed);
        revealed = nextRevealed;
      }
      render(response);
    } finally {
      setBusy(false);
    }
  }

  function setBusy(on) {
    busy = on;
    app.setAttribute('aria-busy', String(on));
  }

  function render(response) {
    lastResponse = response;
    const flips = new Set(response.recommendation.flips.map(([i, j]) => `${i},${j}`));
    tiles.forEach((row, i) => row.forEach((tile, j) => {
      const cell = response.cells[i][j];
      tile.classList.toggle('revealed', cell.revealed);
      face(tile).src = sprite(cell.revealed ? FACES[cell.options[0]] : 'card_back');
      for (let k = 0; k < 4; k++) tile.classList.toggle(`can-${k}`, !cell.revealed && cell.options.includes(k));
      const uncertain = !cell.revealed && cell.voltorb > 0 && cell.voltorb < 1;
      $('.odds', tile).textContent = uncertain ? percent(cell.voltorb) : '';
      tile.title = cell.revealed
        ? `Flipped: ${cell.options[0] || 'Voltorb'}`
        : `Could be ${cell.options.map((o) => o || 'Voltorb').join(', ')}\nVoltorb ${percent(cell.voltorb)}, 2 or 3 ${percent(cell.multiplier)}`;
      setPending(tile, flips.has(`${i},${j}`));
    }));
    drawCoins('current-coins', response.coins);

    if (response.status === 'playing') return enterFlip(response);
    phase = 'over';
    overByDone = false;
    app.classList.remove('flipping');
    if (response.status === 'won') {
      bank(response.coins);
      say(`Game clear!\nEvery 2 and 3 is flipped.\nYou got ${response.coins} Coins!`);
    } else {
      say('Oh no! You get 0 Coins!');
    }
    setMenu([{ label: 'New game', run: newGame }, { label: 'Back', run: back }]);
    actionButtons[0].focus();
  }

  function enterFlip(response) {
    phase = 'flip';
    app.classList.add('flipping');
    const { flips, safe, risk } = response.recommendation;
    const fit = `${plural(response.boards, 'board')} still fit.`;
    say(safe
      ? `Flip the ${plural(flips.length, 'marked card')}, then enter what each showed.\n${fit}`
      : `No card is sure to be safe.\nFlip the marked card: ${percent(risk)} chance of a Voltorb.\n${fit}`);
    setMenu([
      { label: 'Next', run: () => submit() },
      { label: 'Found all 2s & 3s', run: done, title: "End the round: every 2 and 3 has been flipped" },
      { label: 'Back', run: back },
    ]);
    const first = pendingTiles()[0];
    if (first) flipInput(first).focus();
  }

  function submit() {
    if (busy) return;
    if (phase === 'counts') return solve(revealed);
    if (phase !== 'flip') return;
    const pending = pendingTiles();
    const blank = pending.find((tile) => flipInput(tile).value === '' && !tile.classList.contains('manual'));
    if (blank) {
      return say('Enter what each marked card showed: 1, 2, 3, or 0 for a Voltorb.', flipInput(blank));
    }
    const next = revealed.map((row) => row.slice());
    for (const tile of pending) {
      const value = flipInput(tile).value;
      if (value === '') continue;
      const [i, j] = position(tile);
      next[i][j] = Number(value);
    }
    return solve(next);
  }

  function done() {
    phase = 'over';
    overByDone = true;
    app.classList.remove('flipping');
    pendingTiles().forEach((tile) => setPending(tile, false));
    const coins = lastResponse ? lastResponse.coins : 0;
    bank(coins);
    say(`Game clear!\nYou got ${coins} Coins!`);
    setMenu([{ label: 'New game', run: newGame }, { label: 'Back', run: back }]);
    actionButtons[0].focus();
  }

  function back() {
    if (phase === 'over') unbank();
    if (phase === 'over' && overByDone) return solve(revealed);
    if (history.length) {
      revealed = history.pop();
      return solve(revealed); // the same grid, so solve() doesn't push it back
    }
    enterCounts();
  }

  function clearBoard() {
    for (const tile of allTiles) {
      tile.classList.remove('revealed', 'can-0', 'can-1', 'can-2', 'can-3');
      tile.removeAttribute('title');
      $('.odds', tile).textContent = '';
      setPending(tile, false);
      face(tile).src = sprite('card_back');
    }
    drawCoins('current-coins', 0);
  }

  function enterCounts() {
    phase = 'counts';
    app.classList.remove('flipping');
    lastResponse = null;
    clearBoard();
    setMenu([
      { label: 'Solve', run: () => submit() },
      { label: 'Clear counters', run: clearCounts },
    ]);
    const firstEmpty = [...rows, ...cols].flatMap(({ value, voltorbs }) => [value, voltorbs]).find((input) => input.value === '');
    say("Enter each row's points and Voltorbs, then each column's.\nEnter: solve", firstEmpty || rows[0].value);
  }

  function clearCounts() {
    for (const { value, voltorbs } of [...rows, ...cols]) value.value = voltorbs.value = '';
    enterCounts();
  }

  function newGame() {
    revealed = grid(() => null);
    history = [];
    banked = 0;
    overByDone = false;
    clearCounts();
  }

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' || event.target instanceof HTMLButtonElement) return;
    event.preventDefault();
    submit();
  });

  // ---------- fit the app to the window at a whole-number zoom ----------

  function fit() {
    const zoomFor = (stacked) => {
      app.classList.toggle('stacked', stacked);
      app.style.setProperty('--zoom', '1');
      const { width, height } = app.getBoundingClientRect();
      return Math.floor(Math.min((innerWidth - 8) / width, (innerHeight - 8) / height));
    };
    const wide = zoomFor(false);
    const stacked = zoomFor(true);
    app.classList.toggle('stacked', stacked > wide);
    app.style.setProperty('--zoom', String(Math.max(1, wide, stacked)));
  }
  addEventListener('resize', fit);
  fit();
  document.fonts.ready.then(fit);

  addToTotal(0);
  enterCounts();
})();
