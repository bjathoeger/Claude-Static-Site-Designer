/* Language switching for a static site (the very basics).
 *
 * Markup (the source language stays in the HTML, so a page works without this script):
 *   <html lang="en" data-site-root="../">        data-site-root: the path from this page to the site root
 *   <h1 data-i18n="hero.title">…</h1>            inner HTML is replaced by i18n/<lang>.json → text["hero.title"]
 *   <img alt="…" data-i18n-alt="hero.img">       an attribute is replaced from attr["hero.img"]
 *   <button data-lang-switch="sv">Svenska</button>  the language picker (aria-current marks the current language)
 *   <title data-i18n="meta.title">…</title>      works for the title too
 *
 * The language comes from ?lang=xx, else the visitor's last choice (localStorage), else the source language.
 * There is no automatic redirect by browser language. Links inside the site carry ?lang=xx while a language other
 * than the source is showing, so a shared link opens in the same language.
 * Languages are listed in site.json ("languages": [{"code": "en", "name": "English", "source": true}, …]).
 * Fires "i18n:change" on document (detail: {lang}) after every switch, for scripts that build text themselves.
 */
(function () {
  'use strict';
  var html = document.documentElement;
  var root = html.getAttribute('data-site-root') || './';
  var KEY = 'site-lang';
  var cache = {};
  var original = null;      // the source language, read from the page on the first switch
  var site = null;

  function store(v) { try { if (v) localStorage.setItem(KEY, v); else localStorage.removeItem(KEY); } catch (e) {} }
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function fromUrl() { try { return new URL(location.href).searchParams.get('lang'); } catch (e) { return null; } }

  function load(path) {
    if (!cache[path]) {
      cache[path] = fetch(root + path, { cache: 'no-cache' }).then(function (r) {
        if (!r.ok) throw new Error(path + ': ' + r.status);
        return r.json();
      });
    }
    return cache[path];
  }

  function snapshot() {
    if (original) return;
    original = { text: {}, attr: {} };
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      original.text[el.getAttribute('data-i18n')] = el.innerHTML;
    });
    document.querySelectorAll('*').forEach(function (el) {
      for (var i = 0; i < el.attributes.length; i++) {
        var a = el.attributes[i].name;
        if (a.indexOf('data-i18n-') === 0) {
          var at = a.slice(10), key = el.attributes[i].value;
          if (!(key in original.attr)) original.attr[key] = el.getAttribute(at);
        }
      }
    });
  }

  function apply(t) {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var v = t.text[el.getAttribute('data-i18n')];
      if (v != null) el.innerHTML = v;
    });
    document.querySelectorAll('*').forEach(function (el) {
      for (var i = 0; i < el.attributes.length; i++) {
        var a = el.attributes[i].name;
        if (a.indexOf('data-i18n-') === 0) {
          var v = t.attr[el.attributes[i].value];
          if (v != null) el.setAttribute(a.slice(10), v);
        }
      }
    });
  }

  function source() {
    var s = (site.languages || []).filter(function (l) { return l.source; })[0];
    return s ? s.code : (html.getAttribute('lang') || 'en');
  }

  function known(code) {
    return (site.languages || []).some(function (l) { return l.code === code; });
  }

  function markLinks(code) {
    var src = source();
    document.querySelectorAll('a[href]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || /^(#|mailto:|tel:|javascript:)/.test(href) || a.hasAttribute('data-lang-switch')) return;
      var u;
      try { u = new URL(href, location.href); } catch (e) { return; }
      if (u.origin !== location.origin) return;
      if (code === src) u.searchParams.delete('lang'); else u.searchParams.set('lang', code);
      a.setAttribute('href', u.pathname + u.search + u.hash);
    });
  }

  function markPicker(code) {
    document.querySelectorAll('[data-lang-switch]').forEach(function (el) {
      if (el.getAttribute('data-lang-switch') === code) el.setAttribute('aria-current', 'true');
      else el.removeAttribute('aria-current');
    });
  }

  function setUrl(code) {
    try {
      var u = new URL(location.href);
      if (code === source()) u.searchParams.delete('lang'); else u.searchParams.set('lang', code);
      history.replaceState(history.state, '', u.pathname + u.search + u.hash);
    } catch (e) {}
  }

  function show(code) {
    if (!known(code)) code = source();
    snapshot();
    var done = function () {
      html.setAttribute('lang', code);
      markPicker(code);
      markLinks(code);
      html.classList.remove('i18n-pending');
      document.dispatchEvent(new CustomEvent('i18n:change', { detail: { lang: code } }));
    };
    if (code === source()) { apply(original); done(); return Promise.resolve(); }
    return load('i18n/' + code + '.json').then(function (t) { apply(t); done(); })
      .catch(function (e) { console.error('i18n:', e); html.classList.remove('i18n-pending'); });
  }

  window.siteLanguage = {
    set: function (code) { store(code); setUrl(code); return show(code); },
    get: function () { return html.getAttribute('lang'); }
  };

  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-lang-switch]');
    if (!el) return;
    e.preventDefault();
    window.siteLanguage.set(el.getAttribute('data-lang-switch'));
  });

  load('site.json').then(function (s) {
    site = s;
    var want = fromUrl() || stored() || source();
    if (!known(want)) want = source();
    store(want === source() && !fromUrl() ? null : want);
    setUrl(want);
    return show(want);
  }).catch(function (e) { console.error('i18n:', e); html.classList.remove('i18n-pending'); });
})();
