      // vars

      var url = "http://jsonbot.appspot.com/gadgetexec/";
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
      var consoletxt = '<div align="center"><form><b>&lt;-</b><input length="50" type="text" name="cmnd" onKeyPress="return doexec(this.form, event);" /><b>-&gt;</b></form></div><div class="body" align="center" id="content_div"><i>no command given yet.</i></div>';
      var feedstxt = '<div class="bndy" align="left"><form name="feeddata" action="return dosubmit(this.form, event);" method="GET"><b>feed name - </b> <input type="text" name="name" /><br></b><b>feed url - </b> <input type="text" name="url" onKeyPress="return doenter(this.form, event);" /><br><br><input type="submit" name="Enter" onClick="return dosubmit(this.form, event);"/><input type="reset" name="reset" /></form><div class="body" align="left" id="content_div"><i>no feeds entered yet.</i></div></div>';

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

      // start function .. call on load of applet

      function start() {
        if (!viewerid) {
          viewerid = window.location.host;
        }
        if (!waveid) {
          waveid = wave.getWaveId();
        }

        var txt = "enter a command in the box above.";
        output(txt);

        if (wave && wave.isInWaveContainer()) {
           doCmnd("hb-welcome", dotop);
        }

        statusadd('done');
        // gadgets.window.adjustHeight();
      }

      // mainloop

     function loop() {
        doCmnd("outputcache", dobottom); 
        lastpolled = new Date();
        //var lpdate = lastpolled.getTime();
        status("last polled at " + lastpolled.toUTCString());
     }


      // INIT

      function consoleinit() {
        doconsole();
        status("booting");
        setCookie();
        // showfeeds();
        statusadd(" - done");
        setInterval("loop();", 300000)
        bottom("started main loop")
        showplugins()
      }

      function setCookie() {
        var val = localStorage && localStorage.getItem("jsb_cookie");
        if (!val) {
            val = identtime.getTime();
            localStorage && localStorage.setItem("jsb_cookie", val);
        }
        statusadd(" - " + val);
      } 

      // function to launch on enter in the command box

      function doenter(form, e) {
        var keycode;
        if (window.event) keycode = window.event.keyCode;
           else if (e) keycode = e.which;
        else return true;
        if (keycode == 13)
        {
           cmnd = "hb-register " + form.name.value + " " + form.url.value;           
           doCmnd(cmnd, response, "output");
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
           doCmnd(cmnd, response, "output");
           form.cmnd.value = "";
           form.focus();
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

      function footer(text) {
        var html = "<i>";
        html += text;
        html += "</i>";

        var element = document.getElementById("footer_div");  
        element.innerHTML = html;
      }

      function topper(text) {
        var html = "<b><i>" + text + "</i></b>";
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

      function showplugins() {
        doCmnd('list', dobottom);
      }

      function doconsole() {
        doscreen(consoletxt);
        document.forms[0].cmnd.focus();
        doCmnd('version', dotop);
        showplugins();
      }

      function dofeeds() {
        doscreen(feedstxt);
        doCmnd("feeds", dotop);
      }

