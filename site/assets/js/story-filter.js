/* All stories: topic filter (panel and the header's topic shortcuts), sort, live search by title, "Load more".
 * Behaviour from handoffs/abigail1/handoff-2026-10-23 (abigail1-a HANDOFF comment and the source's renderVals()).
 * Without this script every story is listed, newest first.
 */
(function () {
  'use strict';
  var section = document.getElementById('all-stories');
  if (!section) return;
  var PAGE = 9;
  var grid = section.querySelector('.grid');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var empty = grid.querySelector('.empty');
  var more = section.querySelector('.more');
  var fbtn = section.querySelector('.fbtn');
  var panel = document.getElementById('topic-panel');
  var status = section.querySelector('.status');
  var input = section.querySelector('.search input');
  var state = { topic: 'All', sort: 'new', q: '', more: false };

  var posts = cards.map(function (el) {
    return { el: el, cat: el.getAttribute('data-cat'), date: el.getAttribute('data-date'), title: el.querySelector('h3').textContent.trim() };
  });

  function list() {
    var q = state.q.toLowerCase();
    var L = posts.filter(function (p) {
      return (state.topic === 'All' || p.cat === state.topic) && (!q || p.title.toLowerCase().indexOf(q) >= 0);
    });
    return L.sort(function (a, b) {
      if (state.sort === 'old') return a.date.localeCompare(b.date);
      if (state.sort === 'az') return a.title.localeCompare(b.title);
      return b.date.localeCompare(a.date);
    });
  }

  function press(sel, attr, value) {
    document.querySelectorAll(sel).forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute(attr) === value ? 'true' : 'false');
    });
  }

  function statusText() {
    var t = state.topic === 'All' ? status.getAttribute('data-all') : state.topic;
    t += ' · ' + status.getAttribute('data-' + state.sort);
    if (state.q) t += ' · ' + status.getAttribute('data-match').replace('{q}', state.q);
    return t;
  }

  function render() {
    var L = list();
    var shown = state.more ? L : L.slice(0, PAGE);
    posts.forEach(function (p) { p.el.hidden = true; });
    L.forEach(function (p) { grid.insertBefore(p.el, empty); });
    shown.forEach(function (p) { p.el.hidden = false; });
    empty.hidden = L.length > 0;
    more.hidden = state.more || L.length <= PAGE;
    press('[data-topic]', 'data-topic', state.topic);
    press('[data-sort]', 'data-sort', state.sort);
    fbtn.querySelector('.cur').textContent = state.topic === 'All' ? status.getAttribute('data-all') : state.topic;
    var s = statusText();
    if (status.textContent !== s) status.textContent = s;
    return L;
  }

  function open(on) {
    panel.hidden = !on;
    fbtn.setAttribute('aria-expanded', on ? 'true' : 'false');
  }

  function pick(topic) {
    state.topic = topic;
    state.more = false;
    open(false);
    render();
  }

  fbtn.addEventListener('click', function () { open(panel.hidden); });

  panel.addEventListener('click', function (e) {
    var b = e.target.closest('[data-topic]');
    if (!b) return;
    pick(b.getAttribute('data-topic'));
    fbtn.focus();
  });

  // the header's topic shortcuts set the same filter and bring the stories into view
  document.querySelectorAll('.bh [data-topic]').forEach(function (b) {
    b.addEventListener('click', function () {
      pick(b.getAttribute('data-topic'));
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      section.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
  });

  section.querySelectorAll('[data-sort]').forEach(function (b) {
    b.addEventListener('click', function () { state.sort = b.getAttribute('data-sort'); render(); });
  });

  input.addEventListener('input', function () { state.q = input.value.trim(); state.more = false; render(); });

  more.querySelector('button').addEventListener('click', function () {
    state.more = true;
    var L = render();
    if (L[PAGE]) L[PAGE].el.focus();
  });

  section.querySelector('.bar').addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) { open(false); fbtn.focus(); }
  });

  document.addEventListener('click', function (e) {
    if (!panel.hidden && !panel.contains(e.target) && !fbtn.contains(e.target)) open(false);
  });

  document.addEventListener('i18n:change', render);

  render();
})();
