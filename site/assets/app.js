window.App = (function(){
  let _data = null
  async function loadData(){
    if(_data) return _data
    try{
      const res = await fetch('/data/recipes.json')
      if(!res.ok) throw new Error('no')
      _data = await res.json()
      return _data
    }catch(e){
      const res = await fetch('data/recipes.json')
      _data = await res.json()
      return _data
    }
  }
  return {loadData}
})()
