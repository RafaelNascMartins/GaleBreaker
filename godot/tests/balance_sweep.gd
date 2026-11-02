extends SceneTree

func _initialize() -> void: call_deferred("run")

func run() -> void:
	var data:=GaleData.new()
	var results:Array=[]
	for a:String in GaleData.IDS:
		for b:String in GaleData.IDS:
			var sim:=GaleCombat.new(data)
			sim.start(a,b,"zephyr_dojo","versus",[],[])
			sim.countdown=0
			var ticks:=0
			for frame in 24000:
				var swap:Dictionary=sim.p1
				sim.p1=sim.p2;sim.p2=swap
				var input1:=sim.ai_input(true)
				swap=sim.p1;sim.p1=sim.p2;sim.p2=swap
				var input2:=sim.ai_input(true)
				sim.step(input1,input2)
				ticks=frame+1
				if sim.winner!=0:break
			results.append({"p1":a,"p2":b,"winner":sim.winner,"ticks":ticks,"hp1":sim.p1.hp,"hp2":sim.p2.hp,"wins":sim.wins})
			print("BALANCE ",a," vs ",b,": ",sim.winner," in ",ticks," ticks")
	var path:=ProjectSettings.globalize_path("res://../art-source/previews/balance-report.json")
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify(results,"  "))
	var unfinished:=results.filter(func(result:Dictionary)->bool:return result.winner==0).size()
	print("BALANCE SWEEP: ",results.size()," matchups, ",unfinished," unfinished")
	quit(1 if unfinished>0 else 0)
