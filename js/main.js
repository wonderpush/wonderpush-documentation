// closure for strict mode
(function() {
"use strict";

window.Docs = {
  get: function(selector, node, tag) {
    if(!selector)
    {
      if(node)
      {
        node = Docs.get(node);
        return (node && node.nodeType != 3 && tag) ? node.getElementsByTagName(tag) : null;
      }else{
        return null;
      }
    }

    if (selector.nodeType) {
      return selector;
    } else {
      if (selector.length > 0 && selector.charAt(0) != '.') {
        return document.getElementById(selector);
      } else {
        var cls = selector.substring(1);
        var classElements = [];
        if (!node){
          node = document;
        }
        else if (this.isString(node)) {
          node = document.getElementById(node);
          if(!node) return [];
        }

        if (!tag) tag = '*';
        var els = node.getElementsByTagName(tag);
        var elsLen = els.length;
        var pattern = new RegExp('(^|\\s)' + cls + '(\\s|$)');
        for (var i = 0, j = 0; i < elsLen; i++) {
          if (pattern.test(els[i].className)) {
            classElements[j] = els[i];
            j++;
          }
        }
        els = null;
        pattern = null;
        return classElements;
      }
    }
  },

  getFirst:function(selector, node, tag){
    var els = Docs.get(selector, node, tag);
    if(els && els.length !== undefined) // this is an array-like object (NodeList and HTMLCollection are not "instanceof Array")
    {
      return els.length ? els[0] : null; // empty or not ?
    }
    return els; // not an array : domEl or null
  },

  isDescendant: function(node, ancestor){
    while(node != ancestor && node.parentNode){
      node = node.parentNode;
    }
    return node == ancestor;
  },

  isString: function(o){
    return typeof o == 'string';
  },

  trim: function(s){
    return (s || "").replace(/^\s+|\s+$/g, "");
  },

  /*=== CLASS METHODS ===*/
  hasCls: function(node, cls){
    node = this.get(node);
    if (!node || !cls) return false;
    cls = this.trim(cls);
    if (node.classList) {
      return node.classList.contains(cls);
    }
    var pattern = new RegExp('(^|\\s)' + cls + '(\\s|$)');
    return pattern.test(node.className);
  },

  addCls: function(node, cls){
    node = this.get(node);
    if (!node) return null;
    if (cls) {
      cls = this.trim(cls);
      if (node.classList) {
        node.classList.add(cls);
      }
      else {
        var finalClass = node.className;
        if(!this.hasCls(node, cls)) finalClass += ' ' + cls;
        node.className = this.trim(finalClass);
      }
    }
    return node;
  },

  removeCls: function(node, cls){
    node = this.get(node);
    if (!node) return null;
    if (cls) {
      cls = this.trim(cls);
      if (node.classList) {
        node.classList.remove(cls);
      }
      else {
        var i, a = node.className.split(/\s+/);
        for(i=0; i<a.length; i++)
        {
          if(a[i] == cls)
          {
            a.splice(i, 1);
            node.className = a.join(' ');
            break;
          }
        }
      }
    }
    return node;
  }
};

Docs.EventDispatcher =
{
  /**
   * bind an handler to an element for an event
   * @param DOM-elt element
   * @param string eventType example : click, change, focus ...
   * @param function handler function to be executed when event occurs on element
   */
  bind: function(element, eventType, handler)
  {

    if(eventType == 'mouseenter'){
      return this.bind(element, 'mouseover', function(e){
        e = e || window.event;
        var relatedTarget = e.relatedTarget || e.fromElement;
        if(!relatedTarget || !(element === relatedTarget || Docs.isDescendant(relatedTarget, element)))
        {
          handler(e);
        }
      });
    }

    if(eventType == 'mouseleave'){
      return this.bind(element, 'mouseout', function(e){
        e = e || window.event;
        var relatedTarget = e.relatedTarget || e.toElement;
        if(!relatedTarget || !(element === relatedTarget || Docs.isDescendant(relatedTarget, element)))
        {
          handler(e);
        }
      });
    }

    // Bind the global event handler to the element
    var h = function(e){return Docs.EventDispatcher._dispatch(handler,e);};

    if(element.addEventListener)
    {
      element.addEventListener(eventType, h, false);
    }
    else if(element.attachEvent)
    {
      element.attachEvent( "on" + eventType, h);
    }
    return h;
  },

  /**
   * unbind an handler to an element for an event
   * @param DOM-elt element
   * @param string eventType example : click, change, focus ...
   * @param function handler function return by bind
   */
  unbind: function(element, eventType, h)
  {
     if(element.removeEventListener)
     {
       element.removeEventListener(eventType, h, false);
     }
     else if(element.attachEvent)
     {
       element.detachEvent( "on" + eventType, h);
     }
  },

  _dispatch: function(handler,e)
  {
    var evt = (e || window.event);
    if(!evt.target && evt.srcElement)
    {
      evt.target = evt.srcElement;
    }
    if (!evt.currentTarget && this && this !== window)
    {
      evt.currentTarget = this;
    }
    return handler.call(null, evt);
  }

};

Docs.MenuRetractable = {
  //INTERNAL
  _running: false,

  _menus: {},
  _idx: 1,

  _arrowClosed: '<span class="arrow_closed"></span>', //'&#9656;',
  _arrowOpened: '<span class="arrow_opened"></span>', //'&#9662;',

  run: function() {
    if (this._running) {
      this.destroy();
    }

    var i;
    var menus = Docs.get('.menuRetractable');
    for(i=0; i<menus.length; i++) {
      this._registerMenu(menus[i]);
    }

    this._running = true;
  },

  destroy: function() {
    if (this._running) {
      this._unregisterMenus();
      this._running = false;
    }
  },

  _registerMenu: function(el) {
    var idx = el.getAttribute('data-idx');
    if (!idx) {
      el.setAttribute('data-idx', this._idx);
      idx = this._idx;
      this._idx++;
    }
    this._menus[idx] = {
      el: el,
      events: {}
    };
    this._registerClick(idx);
  },

  _unregisterMenu: function(el) {
    var idx = el.getAttribute('data-idx');
    if (this._menus[idx]) {
      this._unregisterDrag(idx);
      delete this._menu[idx];
    }
  },

  _unregisterMenus: function() {
    var idx;
    for (idx in this._menus) {
      this._unregisterMenu(this._menus[idx]);
    }
    this._menus = {};
  },

  _registerClick: function(idx) {
    this._unregisterClick(idx);
    var _this = this;
    this._menus[idx].events.click = Docs.EventDispatcher.bind(this._menus[idx].el, 'click', function(e){_this._onclick(e);});
  },

  _onclick: function(e) {
    var a, s, t = e.target;

    // Allow the arrow or its inner image to be clickable
    if (t && Docs.hasCls(t, 'arrow')) {
      t = t.parentNode;
    } else if (t && Docs.hasCls(t.parentNode, 'arrow')) {
      t = t.parentNode.parentNode;
    }

    if (t && Docs.hasCls(t, 'openable')) {
      s = t.nextElementSibling;
      a = Docs.getFirst('.arrow', t);
      if (s && a) {
        if (Docs.hasCls(s, 'opened')) {
          Docs.removeCls(s, 'opened');
          a.innerHTML = this._arrowClosed;
        }
        else {
          Docs.addCls(s, 'opened');
          a.innerHTML = this._arrowOpened;
        }
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    }
    return true;
  },

  _unregisterClick: function(idx) {
    if (this._menus[idx].events.click) {
      Docs.EventDispatcher.unbind(this._menus[idx].el, 'click', this._menus[idx].events.click);
      this._menus[idx].events.click = null;
      delete this._menus[idx].events.click;
    }
  },

  openSubMenu: function(rootMenu, leafElement) {
    var s, a;
    while (leafElement !== rootMenu) {
      if (leafElement.tagName.toLowerCase() === 'ul') {
        Docs.addCls(leafElement, 'opened');
        s = leafElement.previousElementSibling;
        a = Docs.getFirst('.arrow', s);
        a.innerHTML = this._arrowOpened;
      } else if (leafElement.tagName.toLowerCase() === 'li') {
        Docs.addCls(leafElement, 'selected');
      }
      leafElement = leafElement.parentNode;
    }
  },

  doOpen: function() {
    var main = Docs.get('main');
    var path = window.location.pathname;
    if (path.substr(-1) === '/') path = path.substr(0, path.length-1);
    if (main && path.substr(0,5) === '/docs') {
      var menu = Docs.getFirst('.menuRetractable', main);
      if (menu) {
        var links = Docs.get(null, menu, 'a');
        for (var i=links.length-1; i>=0; i--) {
          if (links[i].hash === '' && links[i].pathname === path) {
            Docs.MenuRetractable.openSubMenu(menu, links[i]);
            break;
          }
        }
      }
    }
  }
};

Docs.MenuButton = {
  init: function() {
    var menu, menuBtn;
    var docPage = Docs.getFirst('.developerDocsPage');
    if (docPage) {
      menu = Docs.getFirst('.halfMenu', docPage);
      menuBtn = Docs.getFirst('.halfMenuBtn', docPage);
    }

    if (menu && menuBtn) {
      var toggle = function() {
        if (Docs.hasCls(menu, 'opened')) {
          Docs.removeCls(menu, 'opened');
        }
        else {
          Docs.addCls(menu, 'opened');
        }
      };
      Docs.EventDispatcher.bind(menuBtn, 'click', toggle);
    }
  }
};

Docs.MenuRetractable.run();
Docs.MenuRetractable.doOpen();
Docs.MenuButton.init();

})();