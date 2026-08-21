
local None = newproxy(true)
getmetatable(None).__tostring = function() return "Fusion.None" end
return None
