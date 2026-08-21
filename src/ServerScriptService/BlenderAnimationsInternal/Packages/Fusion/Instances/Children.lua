
local CHILDREN = newproxy(true)
getmetatable(CHILDREN).__tostring = function() return "Fusion.Children" end
return CHILDREN
