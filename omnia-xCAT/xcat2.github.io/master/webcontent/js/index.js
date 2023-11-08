(function(){
  var cli1 = document.getElementById('client1');
  var cl1 = document.getElementById('cl1');
  var intro1 = document.getElementById('client1_intro');
  var cli2 = document.getElementById('client2');
  var intro2 = document.getElementById('client2_intro');
  var cli3 = document.getElementById('client3');
  var intro3 = document.getElementById('client3_intro');
  var cli4 = document.getElementById('client4');
  var intro4 = document.getElementById('client4_intro');
  var cli5 = document.getElementById('client5');
  var intro5 = document.getElementById('client5_intro');
  var cli6 = document.getElementById('client6');
  var intro6 = document.getElementById('client6_intro');
  var cli7 = document.getElementById('client7');
  var intro7 = document.getElementById('client7_intro');
  var cli8 = document.getElementById('client8');
  var intro8 = document.getElementById('client8_intro');
  var cli9 = document.getElementById('client9');
  var intro9 = document.getElementById('client9_intro');
  var cli10 = document.getElementById('client10');
  var intro10 = document.getElementById('client10_intro');
  var cli11 = document.getElementById('client11');
  var intro11 = document.getElementById('client11_intro');
  var show = document.getElementById('show');
  var timer = null;
  intro1.onmouseover = cli1.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'block';
      cli1.style.opacity = '0.4'; 
      cli1.style.filter = 'alpha(opacity=40)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)'; 
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';    
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)'; 
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)'; 
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)'; 
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)'; 
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)'; 
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)'; 
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'none';
  }
  intro1.onmouseout = cli1.onmouseout = function(){
    timer = setTimeout(function(){
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      show.style.display = 'block';
    },400);

  }
  intro2.onmouseover = cli2.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'block';
      intro4.style.display = 'none';
      intro3.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '0.4';
      cli2.style.filter = 'alpha(opacity=40)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro2.onmouseout = cli2.onmouseout = function(){
    timer = setTimeout(function(){
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro3.onmouseover = cli3.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'block';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '0.4';
      cli3.style.filter = 'alpha(opacity=40)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro3.onmouseout = cli3.onmouseout = function(){
    timer = setTimeout(function(){
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro4.onmouseover = cli4.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'block';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '0.4';
      cli4.style.filter = 'alpha(opacity=40)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro4.onmouseout = cli4.onmouseout = function(){
    timer = setTimeout(function(){
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro5.onmouseover = cli5.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'block';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '0.4';
      cli5.style.filter = 'alpha(opacity=40)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro5.onmouseout = cli5.onmouseout = function(){
    timer = setTimeout(function(){
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro6.onmouseover = cli6.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'block';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '0.4';
      cli6.style.filter = 'alpha(opacity=40)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro6.onmouseout = cli6.onmouseout = function(){
    timer = setTimeout(function(){
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro7.onmouseover = cli7.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'block';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '0.4';
      cli7.style.filter = 'alpha(opacity=40)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro7.onmouseout = cli7.onmouseout = function(){
    timer = setTimeout(function(){
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro8.onmouseover = cli8.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'block';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '0.4';
      cli8.style.filter = 'alpha(opacity=40)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro8.onmouseout = cli8.onmouseout = function(){
    timer = setTimeout(function(){
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);

  }
  intro9.onmouseover = cli9.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'block';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '0.4';
      cli9.style.filter = 'alpha(opacity=40)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro9.onmouseout = cli9.onmouseout = function(){
    timer = setTimeout(function(){
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);
  }
  intro10.onmouseover = cli10.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'block';
      intro11.style.display = 'none';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '0.4';
      cli10.style.filter = 'alpha(opacity=40)';
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      show.style.display = 'none';
  }
  intro10.onmouseout = cli10.onmouseout = function(){
    timer = setTimeout(function(){
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);
  }
  intro11.onmouseover = cli11.onmouseover = function(){
    if(timer) clearTimeout(timer)
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'block';
      cl1.style = 'none';
      cli1.style.opacity = '1';
      cli1.style.filter = 'alpha(opacity=100)';
      cli2.style.opacity = '1';
      cli2.style.filter = 'alpha(opacity=100)';
      cli3.style.opacity = '1';
      cli3.style.filter = 'alpha(opacity=100)';
      cli4.style.opacity = '1';
      cli4.style.filter = 'alpha(opacity=100)';
      cli5.style.opacity = '1';
      cli5.style.filter = 'alpha(opacity=100)';
      cli6.style.opacity = '1';
      cli6.style.filter = 'alpha(opacity=100)';
      cli7.style.opacity = '1';
      cli7.style.filter = 'alpha(opacity=100)';
      cli8.style.opacity = '1';
      cli8.style.filter = 'alpha(opacity=100)';
      cli9.style.opacity = '1';
      cli9.style.filter = 'alpha(opacity=100)';
      cli10.style.opacity = '1';
      cli10.style.filter = 'alpha(opacity=100)';
      cli11.style.opacity = '0.4';
      cli11.style.filter = 'alpha(opacity=40)';
      show.style.display = 'none';
  }
  intro11.onmouseout = cli11.onmouseout = function(){
    timer = setTimeout(function(){
      cli11.style.opacity = '1';
      cli11.style.filter = 'alpha(opacity=100)';
      cli1.style.opacity = '0.4';
      cli1.style.filter = 'alpha(opacity=40)';
      intro1.style.display = 'none';
      intro2.style.display = 'none';
      intro3.style.display = 'none';
      intro4.style.display = 'none';
      intro5.style.display = 'none';
      intro6.style.display = 'none';
      intro7.style.display = 'none';
      intro8.style.display = 'none';
      intro9.style.display = 'none';
      intro10.style.display = 'none';
      intro11.style.display = 'none';
      show.style.display = 'block';
    },400);
  }

})();
