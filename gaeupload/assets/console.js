      // vars

      var url = "http://jsonbot.appspot.com/gadgetexec/";
      var starttime = new Date();
      var interval_id;
      var lastpolled = new Date();
      var sleeptime = 300000;
      var host = "";
      var viewer = "";
      var hostid = "";
      var viewerid = "";
      var parameters = ""
      var identtime = new Date();
      var consoletxt = '<div align="center"><form><b>&lt;-</b><input length="50" type="text" name="cmnd" onKeyPress="return doexec(this.form, event);" /><b>-&gt;</b></form></div><div class="body" align="center" id="content_div"><i>no command given yet.</i></div>';
      var feedstxt = '<form name="feeddata" action="return dosubmit(this.form, event);" method="GET"><b>feed name - </b> <input type="text" name="name" /><br></b><b>feed url - </b> <input type="text" name="url" onKeyPress="return doenter(this.form, event);" /><br><br><input type="submit" name="Enter" onClick="return dosubmit(this.form, event);"/><input type="reset" name="reset" /></form><div class="body" align="center" id="content_div"><i>no feeds entered yet.</i></div>';
      var request = new window.XMLHttpRequest();

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

      // INIT

      function init() {
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


      // INIT

      function consoleinit() {
        statusadd("initialising ... ");
        doconsole();
        setInterval("loop();", 60000)
        status("booting");
        setCookie();
        // showfeeds();
        if (wave) {
            waveid = wave.getWaveId();
            wave.setStateCallback(stateUpdated);
            setTimeout("start();", 500);
        }
        statusadd(" .. done");
      }

      function setCookie() {
        val = localStorage && localStorage.getItem("jsb_cookie");
        if (!val) {
            val = identtime.getTime();
            localStorage && localStorage.setItem("jsb_cookie", val);
        }
        statusadd(" (" + val + ")");
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
           doCmnd(cmnd, response, "output");
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

      function doscreen(screentxt) {
        var element = document.getElementById("screen_div");  
        element.innerHTML = screentxt;
      }

      // response functions

      function response() {
          statusadd(" - " + request.readyState.toString())
          if (request.readyState==4){
              statusadd(" - " + request.status)
              if (request.status==200) {
                   statusadd(" - response ok");
                   output(request.responseText);
              }
              else {
                   statusadd(" - response NOT ok");
                   output("no result");
              }
          }
      }

      function dotop(obj) {
        topper(obj.text);
      }

      function dostatus(obj) {
        status(obj.text);
      }

      if (wave) {
          function doCmnd(cmnd, resp, how) {
              var params = {}   
              var postdata = {  
                  content : cmnd, 
                  waveid : waveid,
                  who : viewerid
                  }

              params[gadgets.io.RequestParameters.METHOD] = gadgets.io.MethodType.POST;
              params[gadgets.io.RequestParameters.POST_DATA] = gadgets.io.encodeValues(postdata);

              if (resp) {
                  gadgets.io.makeRequest(url, resp, params);
              }
              else {
                  gadgets.io.makeRequest(url, response, params);
              }
          }
      }
      else {
          function doCmnd(cmnd, resp, how) {
              status("sending command ");
              parameters="content="+encodeURIComponent(cmnd);
              request.onreadystatechange = response;
              request.open("POST", url);
              request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
              request.setRequestHeader("Cache-Control", "no-cache");
              request.send(parameters);
          }
      }

      function doconsole() {
        doscreen(consoletxt);
        status(viewerid);
        //showplugins();
        topper("enter a command.");
      }

      function dofeeds() {
        doscreen(feedstxt);
        status(viewerid);
        // showfeeds();
        topper("enter a feed name and url.")
      }

     function loop(sleep) {
        status("last polled at " + lpdate.toUTCString());
        doCmnd("outputcache", dotop); 
        lastpolled = new Date();
        lpdate = lastpolled.getTime();
     }

     if (gadgets) { 
         gadgets.util.registerOnLoadHandler(init);
     }
