
return function(task_)
    if type(task_) == "function" then task_()
    elseif typeof(task_) == "RBXScriptConnection" then task_:Disconnect()
    elseif typeof(task_) == "Instance" then task_:Destroy()
    elseif type(task_) == "table" then
        for _, t in ipairs(task_) do require(script)(t) end
    end
end
