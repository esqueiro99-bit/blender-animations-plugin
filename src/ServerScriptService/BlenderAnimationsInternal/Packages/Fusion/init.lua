
-- Fusion 0.2.x - Public API
local Fusion = {}

-- Lazy load submodules relative to this script
local function req(name)
    return require(script[name])
end

-- Core constructors
Fusion.New         = req("Instances").New
Fusion.Hydrate     = req("Instances").Hydrate
Fusion.Children    = req("Instances").Children
Fusion.OnEvent     = req("Instances").OnEvent
Fusion.OnChange    = req("Instances").OnChange
Fusion.Ref         = req("Instances").Ref
Fusion.Out         = req("Instances").Out
Fusion.Cleanup     = req("Instances").Cleanup

-- State
Fusion.Value       = req("State").Value
Fusion.Computed    = req("State").Computed
Fusion.Observer    = req("State").Observer
Fusion.ForPairs    = req("State").ForPairs
Fusion.ForKeys     = req("State").ForKeys
Fusion.ForValues   = req("State").ForValues

-- Animation
Fusion.Tween       = req("Animation").Tween
Fusion.Spring      = req("Animation").Spring

-- Utility
Fusion.cleanup     = req("Utility").cleanup
Fusion.doNothing   = req("Utility").doNothing
Fusion.None        = req("Utility").None

return Fusion
