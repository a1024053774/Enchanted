deadline=time.monotonic()+15
while True:
    observed={manifest['cli']['pid']:probe_process(manifest['cli']['pid'])} if manifest and manifest.get('cli') else {}
    verdict=cli_exit_verdict(attempted,manifest,observed)
    result['cli_exit_verdict']=verdict;save()
    if verdict['status']=='PASS':break
    if verdict['reason']!='recorded_cli_still_alive' or time.monotonic()>=deadline:
        result['status']='BLOCKED';raise RuntimeError(verdict['reason'])
    time.sleep(.05)
