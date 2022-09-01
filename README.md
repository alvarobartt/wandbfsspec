# 🍱 `fsspec` interface for Weights & Biases (wandb)

Quoting Weights and Biases (wandb), "Weights & Biases is the 
machine learning platform for developers to build better models 
faster. Use W&B's lightweight, interoperable tools to quickly track 
experiments, version and iterate on datasets, evaluate model performance, 
reproduce models, visualize results and spot regressions, and share 
findings with colleagues.". Reference at https://docs.wandb.ai/

So you may be thinking, what does `wandb` have to do with anything
close to a File System? Well, it's not but it actually provides a way
to upload/download files and store them in a remote, which makes it somehow
a File System. Also, `wandb` provides an API that lets you interact with
that "File System", so this is why `wandbfsspec` makes sense, in order to ease
that interface between `wandb`'s File System and anyone willing to use it.

The `wandbfsspec` implementation is based on https://github.com/fsspec/filesystem_spec.

## 🔮 Future TODOs

Obviously, since `wandb`'s main purpose is to track and monitor ML experiments,
it contains an artifact store, so as to dump there the experiment artifacts for data
versioning and model tracking. More information in https://wandb.ai/site/artifacts.

So on, a new interface will be implemented in `wandbfsspec` not just to handle the files
that can be uploaded/downloaded to/from `wandb`, but also the artifacts. So the next release
will implement a new `AbstractFileSystem` class named `WandbArtifactStore` with the protocol
`wandbas` in order to access the artifact store as if it was a default File System.

Some more notes on how to actually use `wandb`'s artifact store at https://docs.wandb.ai/guides/artifacts.

## 🚸 Usage

Here's an example on how to locate and open a file:

```python
>>> from wandbfsspec.core import WandbFileSystem
>>> fs = WandbFileSystem(api_key="YOUR_API_KEY")
>>> fs.ls("alvarobartt/wandbfsspec-tests/3s6km7mp")
['alvarobartt/wandbfsspec-tests/3s6km7mp/config.yaml', 'alvarobartt/wandbfsspec-tests/3s6km7mp/file.yaml', 'alvarobartt/wandbfsspec-tests/3s6km7mp/files', 'alvarobartt/wandbfsspec-tests/3s6km7mp/output.log', 'alvarobartt/wandbfsspec-tests/3s6km7mp/requirements.txt', 'alvarobartt/wandbfsspec-tests/3s6km7mp/wandb-metadata.json', 'alvarobartt/wandbfsspec-tests/3s6km7mp/wandb-summary.json']
>>> with fs.open("alvarobartt/wandbfsspec-tests/3s6km7mp/file.yaml", "rb") as f:
...     print(f.read())
b'some: data\nfor: testing'
```

📌 Note that it can also be done through `fsspec` as long as `wandbfsspec` is installed:

```python
>>> import fsspec
>>> fs = fsspec.filesystem("wandbfs")
>>> fs.ls("alvarobartt/wandbfsspec-tests/3s6km7mp")
['alvarobartt/wandbfsspec-tests/3s6km7mp/config.yaml', 'alvarobartt/wandbfsspec-tests/3s6km7mp/file.yaml', 'alvarobartt/wandbfsspec-tests/3s6km7mp/files', 'alvarobartt/wandbfsspec-tests/3s6km7mp/output.log', 'alvarobartt/wandbfsspec-tests/3s6km7mp/requirements.txt', 'alvarobartt/wandbfsspec-tests/3s6km7mp/wandb-metadata.json', 'alvarobartt/wandbfsspec-tests/3s6km7mp/wandb-summary.json']
>>> with fs.open("alvarobartt/wandbfsspec-tests/3s6km7mp/file.yaml", "rb") as f:
...     print(f.read())
b'some: data\nfor: testing'
```

## 📝 Documentation

Coming soon... (https://github.com/mkdocs/mkdocs)

## 🧪 How to test it

In order to test it, you should first set the following environment variables
so as to use `wandb` as a file system for the tests.

```
WANDB_ENTITY = ""
WANDB_PROJECT = ""
WANDB_API_KEY = ""
```

Both entity and project values can be found in your https://wandb.ai/ account, as
the entity name is your account name, and the project name can either be already
created or you can just specify it and it'll be created during `pytest` init. Then,
regarding the API Key, you just need to go to https://wandb.ai/settings, scroll
down to Danger Zone -> API Keys, and copy your personal API Key from there.

⚠️ Make sure that you don't publish your API Key anywhere, that's why we're defining
it as an environment value, so as to avoid potential issues on commiting code with
the actual API Key value.

Then, in order to actually run the tests you can either run:

- `poetry run pytest`
- `poetry run make tests`

Or, if you're not using `poetry`, you can just run both those commands without it.