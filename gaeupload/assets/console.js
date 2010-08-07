      // vars

      //var url = "http://jsonbot.appspot.com/gadgetexec/";
      var url = "http://localhost:8080/gadgetexec/";
      var starttime = new Date();
      var interval_id;
      var lastpolled = new Date();
      var lpdate = lastpolled.getTime();
      var sleeptime = 60000;
      var host = "";
      var viewer = "";
      var hostid = "";
      var viewerid = "";
      var parameters = ""
      var identtime = new Date();
      var consoletxt = '<div align="center"><form><b>&lt;-</b><input length="50" type="text" name="cmnd" onKeyPress="return doexec(this.form, event);" /><b>-&gt;</b></form></div><div class="body" align="center" id="content_div"><i>Welcome to JSONBOT</i></div>';
      var feedstxt = '<div class="body" align="left"><form name="feeddata" action="javascript:submitfeed(this.form);" method="GET"><b>feed name - </b> <input type="text" name="name" /><br></b><b>feed url - </b> <input type="text" name="url" onKeyPress="return doenter(this.form, event);" /><br><br><input type="submit" name="Enter" onClick="return submitfeed(this.form);"/><input type="reset" name="reset" /></form><div class="body" align="left" id="content_div"><i>no feeds entered yet.</i></div></div>';

      // utils functions

      function elapsed() {
        last = new Date();
        diff = last.getTime() - starttime.getTime();
        starttime = last;
        return diff;
      }

      // state 

      function stateUpdated() {
        hostid = wave.getHost().getId();
        viewerid = wave.getViewer().getId();
        topper(hostid + ' ' + viewerid)
      }

      // mainloop

      function loop() {
          doCmnd("outputcache", dobottom); 
          lastpolled = new Date();
          //var lpdate = lastpolled.getTime();
          status("last polled at " + lastpolled.toUTCString());
      }


      // INIT

      function start() {
          setCookie();
          setTimeout("update();", 150);
          setTimeout("doCmnd('help', response);", 3000);
          setInterval("loop();", 300000);
      }


      function init() {
        setTimeout("consolestart();", 10)
      }

      function consolestart() {
          doconsole();
          status("booting");
          start();
          status("booting done");
      }

      function update(what) {
        if (what=="feeds") {
            doCmnd('outputcache', dobottom);
            doCmnd('statusline', doinfo);
            doCmnd('rss-feeds', dotop);
        }
        else {
            doCmnd('outputcache', dobottom);
            doCmnd('statusline', doinfo);
            doCmnd('uptime', dotop);
        }
      }

      function doconsole() {
        doscreen(consoletxt);
        document.forms[0].cmnd.focus();
      }

      function dofeeds() {
        doscreen(feedstxt);
        document.forms[0].name.focus();
      }


      function setCookie() {
        var val = localStorage && localStorage.getItem("jsb_cookie");
        if (!val) {
            val = identtime.getTime();
            localStorage && localStorage.setItem("jsb_cookie", val);
        }
      } 

      // submit feed url to the server

      function submitfeed(form) {
           cmnd = "rss-register " + form.name.value + " " + form.url.value;           
           status("sending command ");
           doCmnd(cmnd, response);
           setTimeout("update();", 500);
           return false;
      } 

      // function to launch on enter in the command box

      function doenter(form, e) {
        var keycode;
        if (window.event) keycode = window.event.keyCode;
           else if (e) keycode = e.which;
        else return true;
        if (keycode == 13)
        {
           cmnd = "rss-register " + form.name.value + " " + form.url.value;           
           status("sending command ");
           doCmnd(cmnd, response);
           setTimeout("update();", 500);
           return false;
        }
        else
          return true;
      }

      function doexec(form, e) {
        var keycode;
        if (window.event) keycode = window.event.keyCode;
           else if (e) keycode = e.which;
        else return true;
        if (keycode == 13) {
           cmnd = form.cmnd.value; 
           status("sending command ");
           doCmnd(cmnd, response);
           form.cmnd.value = "";
           form.focus();
           setTimeout("update();", 500);
           return false;
        }
        else
          return true;
      }

      // output functions

      function output(text) {
        var html = text;
        var element = document.getElementById("content_div");  
        element.innerHTML = html;
      }

      function info(text) {
        var html = "<i>";
        html += text;
        html += "</i>";

        var element = document.getElementById("info_div");  
        element.innerHTML = html;
      }

      function footer(text) {
        var html = "<i>";
        html += text;
        html += "</i>";

        var element = document.getElementById("footer_div");  
        element.innerHTML = html;
      }

      function topper(text) {
        var html = "<i>";
        html += text;
        html += "</i>";
        var element = document.getElementById("topper_div");  
        element.innerHTML = html;
      }

      function statusadd(text) {
        var html = "<i>";
        html += text;
        html += "</i>";

        var element = document.getElementById("status_div");  
        element.innerHTML += html;
      }

      function status(text) {
        var html = "<i>";
        html += text;
        html += "</i>";

        var element = document.getElementById("status_div");  
        element.innerHTML = html;
      }

      function bottom(text) {
        var html = "<b>";
        html += text;
        html += "</b>";

        var element = document.getElementById("bottom_div");  
        element.innerHTML = html;
      }

      function doscreen(screentxt) {
        var element = document.getElementById("screen_div");  
        element.innerHTML = screentxt;
      }

      // response functions

      function response(obj) {
          statusadd(" - " + obj.readyState.toString())
          if (obj.readyState==4){
              statusadd(" - " + obj.status)
              if (obj.status==200) {
                   statusadd(" - response ok");
                   output(obj.responseText);
              }
              else {
                   statusadd(" - response NOT ok");
                   output("no result");
              }
          }
      }

      function dotop(obj) {
          if (obj.readyState==4) {
              if (obj.status==200) {
                  topper(obj.responseText);
              }
          }
      }

      function dostatus(obj) {
           if (obj.readyState==4) {
               if (obj.status==200) {
                   status(obj.responseText);
              }
          }
      }

      function dobottom(obj) {
           if (obj.readyState==4) {
               if (obj.status==200) {
                   bottom(obj.responseText);
              }
          }
      }

      function doinfo(obj) {
           if (obj.readyState==4) {
               if (obj.status==200) {
                   info(obj.responseText);
              }
          }
      }

      function doCmnd(cmnd, resp, how) {
          var request = false;
          if (window.XMLHttpRequest) {
              request = new XMLHttpRequest();
          }
          else if (window.ActiveXObject) { 
              try {
                  request = new ActiveXObject("Msxml2.XMLHTTP");
              } catch (e) {
                  try {
                      request = new ActiveXObject("Microsoft.XMLHTTP");
                  } catch (e) {}
              }
          }
          if (!request) {
              topper("can't make connection to server");
              return false;
          }

          request.onreadystatechange = function () {
              resp(request);
          }

          request.open("POST", url, true);
          request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          request.setRequestHeader("Content-Length", parameters.length);
          request.setRequestHeader("Cache-Control", "no-cache");
          parameters="content="+encodeURIComponent(cmnd);
          request.send(parameters);
          return true;
      }

