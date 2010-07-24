      // vars

      var url = "https://jsonbot.appspot.com/gadgetexec/";
      var starttime = new Date();
      var interval_id;
      var lastpolled = new Date();
      var sleeptime = 300000;
      var host = "";
      var viewer = "";
      var hostid = "";
      var viewerid = "";
      var identtime = new Date();
      var consoletxt = '<form><b>&gt; </b><input length="50" type="text" name="cmnd" onKeyPress="return doexec(this.form, event);" /></form><b>&gt; </b><b><i>results:</i></b><br><br><div class="body" align="left" id="content_div"><i>no command given yet.</i></div>';
      var feedstxt = '<form name="feeddata" action="return dosubmit(this.form, event);" method="GET"><b>feed name - </b> <input type="text" name="name" /><br></b><b>feed url - </b> <input type="text" name="url" onKeyPress="return doenter(this.form, event);" /><br><br><input type="submit" name="Enter" onClick="return dosubmit(this.form, event);"/><input type="reset" name="reset" /></form><b>&gt; <i>results:</i></b><br><br><div class="body" align="left" id="content_div"><i>no feeds entered yet.</i></div>';
      var request = new window.XMLHttpRequest();

      // utils functions

      function elapsed() {
        last = new Date();
        diff = last.getTime() - starttime.getTime();
        starttime = last;
        return diff;
      }

      // INIT

      function consoleinit() {
        doconsole();
        status("booting");
        setCookie();
        // showfeeds();
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
          if (request.readyState) {
              statusadd(" " + request.readyState.toString())
          }
          if (request.readyState==4){
              statusadd(" - " + request.status.toString())
              if (request.status==200) {
                   statusadd(" - response ok")
                   output(request.responseText);
              }
              else {
                   statusadd(" - response NOT ok")
              }
          }
          return false
      }

      function dotop(obj) {
        topper(obj.text);
      }

      function dostatus(obj) {
        status(obj.text);
      }

      function doCmnd(cmnd, resp, how) {
        status("sending command");
        var parameters="content="+encodeURIComponent(cmnd)
        request.onreadystatechange = resp;
        request.open("POST", url);
        //request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        request.send(parameters);
      }

      function doconsole() {
        doscreen(consoletxt);
        status(viewerid);
        //showplugins();
        topper("enter a command.")
      }

      function dofeeds() {
        doscreen(feedstxt);
        status(viewerid);
        // showfeeds();
        topper("enter a feed name and url.")
      }
