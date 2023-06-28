// @ts-ignore
import Catalog from "@components/CatalogRow";
// @ts-ignore
import Header from "./Header";
import { useEffect, useState, useRef } from "react";
import { Gallery } from "react-grid-gallery";



export default function Browser() {
  const [images, setImages] = useState([]);
  const circle = useRef(null);
  const [history, setHistory] = useState([])
  const [lastrender, setLastRender] = useState([])
  const [home, goHome] = useState(true)
  const [pos, setPos] = useState([0, 0])
  const [displayCircle, setDisplay] = useState('none')
  const [gallery, setGalleryImages] = useState([])
  const [resize, setResize] = useState(false)
  const [changetags, setChangeTags] = useState(false)
  const [clearstate, setClearState] = useState(false)

  useEffect(() => {
    fetch(`http://${import.meta.env.VITE_HOSTNAME}:${import.meta.env.VITE_BACKEND_PORT}/random_all`)
      .then((res) => res.json())
      .then((res) => {
        setImages(res);
        setGalleryImages([]);
        setLastRender(res);
        setClearState(!clearstate)
      });
  }, [home]);

  const handleClick = (e: any) => {
    if (gallery.length == 0) {
      fetch(`http://${import.meta.env.VITE_HOSTNAME}:${import.meta.env.VITE_BACKEND_PORT}/get_similar_all`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          img: e.target.src, click: [(e.clientX - e.target.getBoundingClientRect().x) / e.target.getBoundingClientRect().width,
          (e.clientY - e.target.getBoundingClientRect().y) / e.target.getBoundingClientRect().height],
          px: 30 / 2,
          history: history
        }),
      })
        .then((res) => res.json())
        .then((res) => {
          window.scrollTo(0, 0);
          setHistory(res['history'])
          setLastRender(res['history'][0])

          setImages(res['final']);
          setResize(!resize)
          setChangeTags(!changetags)

        });
    }
    else {
      console.log(gallery[e]['src'])
      fetch(`http://${import.meta.env.VITE_HOSTNAME}:${import.meta.env.VITE_BACKEND_PORT}/get_similar_from_search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({

          img: gallery[e]['src'],
          history: history
        }),
      })
        .then((res) => res.json())
        .then((res) => {
          window.scrollTo(0, 0);
          setHistory(res['history'])
          setImages(res['final']);
          setLastRender(res['history'][0])
          setGalleryImages([])

        });
    }
  };
  const handleColor = (e, key, methods, id) => {
    fetch(`http://${import.meta.env.VITE_HOSTNAME}:${import.meta.env.VITE_BACKEND_PORT}/filter_color`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        color: e.target.style.backgroundColor,
        history: lastrender,
        row: key,
        id: id,
        methods: methods
      }),
    })
      .then((res) => res.json())
      .then((res) => {
        setImages(() => {
          if (history.length === 0) { return res }
          else {
            return res[0]
          }
        });
        setLastRender(res)
        setResize(!resize)

      });
  }
  const handleCircle = (e) => {
    setPos([e.clientY - 15, e.clientX - 15])
  }
  const enterCircle = (e) => {
    setDisplay('inline')
  }
  const leaveCircle = (e) => {
    setDisplay('none')
  }

  const handleBack = () => {
    if (history.length < 2) {
      goHome(!home)

    }
    else {
      if (history[1][1] == 'rows') {
        setImages(history[1][0])
        setResize(!resize)
        setChangeTags(!changetags)
        setLastRender(history[1])
      }
      else {
        setGalleryImages(history[1][0])

      }
    }

    setHistory(history.slice(1))
  }
  const handleSearch = (e) => {
    if (e.key == 'Enter') {
      fetch(`http://${import.meta.env.VITE_HOSTNAME}:${import.meta.env.VITE_BACKEND_PORT}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ txt: e.target.value, history: history }),
      })
        .then((res) => res.json())
        .then((res) => {
          window.scrollTo(0, 0);
          setGalleryImages(res['images']);
          setHistory(res['history'])
        });
      e.target.value = ''
    }
  }
  const handleSelectTag = (tags, index) => {
    if (tags.length != 0) {
      fetch(`http://${import.meta.env.VITE_HOSTNAME}:${import.meta.env.VITE_BACKEND_PORT}/select_tags`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tags: tags,
          history: lastrender,
          row: index
        }),
      })
        .then((res) => res.json())
        .then((res) => {
          setImages(res[0]);
          setLastRender(res)
          setResize(!resize)

        });
    }
  }
  const obj = images.map((data: any, key) => (
    <Catalog
      key={key}
      index={key}
      id={data.order}
      data={data}
      onClick={handleClick}
      onMouseMove={handleCircle}
      onMouseEnter={enterCircle}
      onMouseLeave={leaveCircle}
      align="prev"
      onmove={handleCircle}
      handleColor={handleColor}
      resize={resize}
      onmenu={handleSelectTag}
      changetags={changetags}
      clearstate={clearstate}

    />
  ));

  return <div>
    <Header
      back={handleBack} history={history.length} handleSearch={handleSearch} goHome={() => { goHome(!home); setHistory([]) }} />
    <div className="cursor" ref={circle} style={{ top: pos[0], left: pos[1], display: displayCircle }}></div>
    {gallery.length == 0 ? obj : <Gallery
      images={gallery}
      enableImageSelection={false}
      onClick={handleClick}
      rowHeight={320}
      defaultContainerWidth={window.innerWidth}
    />}
  </div>
}
