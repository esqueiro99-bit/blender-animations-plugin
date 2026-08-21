
return function(tasks)
    return function()
        if type(tasks) == "table" then
            for _, t in ipairs(tasks) do
                if type(t) == "function" then t()
                elseif typeof(t) == "RBXScriptConnection" then t:Disconnect()
                elseif typeof(t) == "Instance" then t:Destroy()
                end
            end
        end
    end
end
