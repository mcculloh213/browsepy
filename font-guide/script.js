$.ajax({
    url: "//raw.githubusercontent.com/Keyamoon/IcoMoon-Free/master/Font/selection.json",
    dataType: "json",
    success: function (data) {
        const icons = data.icons;
        //console.log(icons);
        $.each(icons, function (key, icon) {
          //console.log(icon)
          $('#icoMoon').append("<li class=''><i class='icon-" + icon.properties.name + "'></i><p><pre>icon-" + icon.properties.name + "</pre></p></li>");
      	})
    },
    error: function (jqXHR, textStatus, errorThrown) {
      	console.log('ERROR', textStatus, errorThrown);
    }
});
