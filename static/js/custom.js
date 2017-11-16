function showfield(name) {
  var element = document.getElementById('other_option');
  if(name=='Other') element.style.display = "block";
  else element.style.display = "none";
}

function showtable(name) {
	console.log(name)
	var element = document.getElementById('custom_option');
	if (name=='custom') element.style.display = "block";
	else element.style.display = "none";
}